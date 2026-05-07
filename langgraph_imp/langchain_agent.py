import json
import re
import os
import time
from typing import Literal, Optional, TypedDict, List, Dict, Any
from typing_extensions import Required, NotRequired
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field, field_validator, ValidationError
from memory import SimpleMemoryStore
import unicodedata
from data_client import fetch_products, fetch_orders, fetch_faq

# ========================= 0) Lightweight persistent memory =========================
APP_INSTANCE = os.getenv("AURA_APP_INSTANCE_ID") or str(int(time.time()))
MEMORY = SimpleMemoryStore(path="memory_store.json", history_max=8, namespace=APP_INSTANCE)

# ========================= 1) Unified state schema =========================
class AgentState(TypedDict, total=False):
    # Required to start the graph
    user_query: Required[str]

    # OPTIONAL: who is talking (lets us separate memory per user or per session)
    user_id: NotRequired[str]

    # Core outputs
    route: NotRequired[Literal["faq", "products", "orders", "none"]]
    context: NotRequired[Dict[str, Any]]
    answer: NotRequired[str]

    # Memory loaded for this user
    memory: NotRequired[Dict[str, Any]]

    tool_calls: NotRequired[List[Dict[str, Any]]]
    warnings: NotRequired[List[str]]
    errors: NotRequired[List[str]]
    trace_id: NotRequired[str]
    latency_ms: NotRequired[int]
    tokens: NotRequired[Dict[str, int]]
    recommended_ids: NotRequired[List[Any]]


def _norm(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", s).strip().lower()

def extract_recommended_ids_from_answer(answer: str, products: List[Dict[str, Any]]) -> List[Any]:
    """
    Heuristic: if the answer mentions a product's title (case-insensitive, normalized),
    consider it 'recommended'. Fallback: if none matched, return first 2 products.
    """
    if not isinstance(products, list):
        return []

    ans = _norm(answer or "")
    recos: List[Any] = []

    # Try exact/substring title matches
    for p in products:
        title = _norm(str(p.get("title", "")))
        pid = p.get("id") or p.get("pid")
        if title and pid is not None and title in ans:
            recos.append(pid)

    # If nothing matched, assume first 2 shown are the recos
    if not recos:
        for p in products[:2]:
            pid = p.get("id") or p.get("pid")
            if pid is not None:
                recos.append(pid)

    # Deduplicate, keep order
    seen = set()
    recos_unique = []
    for pid in recos:
        if pid not in seen:
            seen.add(pid)
            recos_unique.append(pid)
    return recos_unique


# ========================= 2) LLMs =========================
gen_llm = OllamaLLM(
    model="llama3",    # make sure you've `ollama pull llama3`
    temperature=0.2,
    num_predict=250,
)
router_llm = OllamaLLM(
    model="llama3",
    format="json",
    temperature=0,
    num_predict=128,
)

# ========================= 3) Router output model =========================

class RouteOut(BaseModel):
    route: str = Field(..., description="Chosen route")

    @field_validator("route")
    @classmethod
    def check_route(cls, v):
        if v not in {"products","orders","faq","none"}:
            raise ValueError(
                f"Invalid route '{v}'. Allowed values: products, orders, faq, none."
            )
        return v

# ========================= 4) Memory helpers =========================

SKIN_TYPES = {"dry","oily","combination","sensitive","normal"}
CONCERN_KEYWORDS = {
    "acne": ["acne","breakout","pimple"],
    "redness": ["redness","rosacea","flush"],
    "pigmentation": ["hyperpigmentation","dark spot","melasma","spot"],
    "wrinkle": ["wrinkle","fine line","aging","anti-aging","retinol needed"],
    "dehydration": ["dehydrated","tight","flaky"]
}
ALLERGY_KEYWORDS = {
    "fragrance": ["fragrance","perfume","scented","unscented"],
    "alcohol": ["alcohol"],
    "essential oils": ["essential oil","EO"],
}
INGR_PREFS = {"niacinamide","vitamin c","retinol","aha","bha","pha","ceramide",
              "hyaluronic","hyaluronic acid","azelaic","centella","snail"}
INGR_AVOID_PREFIXES = {"avoid","can’t use","cant use","don’t want","do not want"}

CURRENCY_PAT = re.compile(r"(?:₩\s*|\bkrw\s*|\$)\s?([0-9]{2,6})(?:k)?", re.I)
UNDER_PAT = re.compile(r"\b(under|below|less than)\s*(₩|\$)?\s*([0-9]{2,6})k?\b", re.I)

def _krw_from_text(text: str) -> Optional[int]:
    """
    Parse budgets like 'under ₩30k', 'below 25000', '$25' (approx → KRW),
    'budget 30k', etc. Simple heuristics.
    """
    m = UNDER_PAT.search(text)
    if m:
        amt = int(m.group(3))
        # if user typed '30k', our regex eats '30', but the 'k?' handles suffix.
        # If it looks like <= 500, assume 'k' intended when won symbol present.
        if amt < 500 and (m.group(2) == "₩" or 'k' in text.lower()):
            amt *= 1000
        if m.group(2) == "$":
            return int(amt * 1300)  # rough USD→KRW
        return amt

    m2 = CURRENCY_PAT.search(text)
    if m2:
        amt = int(m2.group(1))
        if "k" in text.lower():
            amt *= 1000
        if "$" in text:
            return int(amt * 1300)
        return amt
    return None

#For the memory, current simplificated implementation is a JSON file
def extract_facts_from_text(text: str) -> Dict[str, Any]:
    """
    Very lightweight, deterministic extraction from the latest user message.
    """
    t = text.lower()
    profile_updates: Dict[str, Any] = {}
    # skin type
    for st in SKIN_TYPES:
        if re.search(rf"\b{re.escape(st)}\b", t):
            profile_updates["skin_type"] = st
            break
    # concerns
    concerns_found = set()
    for name, kws in CONCERN_KEYWORDS.items():
        if any(kw in t for kw in kws):
            concerns_found.add(name)
    if concerns_found:
        profile_updates["concerns"] = sorted(concerns_found)

    # allergies / sensitivities (e.g., "I need fragrance-free", "no fragrance")
    allergies = set()
    if "fragrance-free" in t or "fragrance free" in t or "unscented" in t or "no fragrance" in t:
        allergies.add("fragrance")
    for name, kws in ALLERGY_KEYWORDS.items():
        if any(kw in t for kw in kws):
            allergies.add(name)
    if allergies:
        profile_updates["allergies"] = sorted(allergies)

    # ingredient preferences / avoid
    pref_ings = set()
    for ing in INGR_PREFS:
        if re.search(rf"\b{re.escape(ing)}\b", t):
            pref_ings.add(ing)
    if pref_ings:
        profile_updates["pref_ingredients"] = sorted(pref_ings)

    avoid_ings = set()
    if any(pfx in t for pfx in INGR_AVOID_PREFIXES):
        # collect any ingredient words after avoid-like phrases
        for ing in INGR_PREFS:
            if f"avoid {ing}" in t or f"avoid {ing}s" in t or f"avoid {ing.replace(' ', '')}" in t or ing in t:
                avoid_ings.add(ing)
    # also capture “retinol irritates me”, “can’t use retinol”
    for ing in INGR_PREFS:
        if any(expr in t for expr in [f"can't use {ing}", f"can’t use {ing}", f"{ing} irritates", f"allergic to {ing}"]):
            avoid_ings.add(ing)
    if avoid_ings:
        profile_updates["avoid_ingredients"] = sorted(avoid_ings)

    # budget (KRW)
    krw = _krw_from_text(t)
    if krw is not None:
        profile_updates["budget_krw_max"] = krw

    return {"profile": profile_updates} if profile_updates else {}

def merge_profiles(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    res = dict(old or {})
    for k, v in (new or {}).items():
        if isinstance(v, list):
            existing = set(res.get(k, []))
            existing.update(v)
            res[k] = sorted(existing)
        else:
            res[k] = v
    return res

# ========================= 5) Router node =========================

def backup(route_msg):
    m = re.search(r'"route"\s*:\s*"(products|orders|faq|none)"', (route_msg or "").lower())
    return m.group(1) if m else "none"

def route_node(state: AgentState) -> AgentState:
    sys = """You are a router. Decide the single best route for the user query.
Valid routes:
- "products": product info, recommendations, comparisons, ingredients, in stock information
- "orders": order status, tracking
- "faq": store policies, hours, payments, hours, general rules, returns, shipping details
- "none": greetings/small talk or answerable without store data

Rules:
- If external store data is not required, use "none".
- Skincare recommendations require store data → use "products".
- If uncertain, choose "none".
- Reply with ONLY this JSON object: {"route":"products|orders|faq|none"}
"""
    messages = [SystemMessage(content=sys), HumanMessage(content=state["user_query"])]
    route_msg = router_llm.invoke(messages)

    for _ in range(2):
        try:
            data = json.loads(route_msg)
            route = RouteOut(**data)
            return {**state, "route": route.route}
        except (json.JSONDecodeError, ValidationError) as e:
            error_msg = str(e)
        except Exception as e:
            error_msg = str(e)

        agent_out = AIMessage(content=route_msg)
        repair = HumanMessage(
            content=(
                "Your previous output was invalid.\n"
                f"Error: {error_msg}\n"
                'Return ONLY valid JSON exactly like: {"route":"products|orders|faq|none"}'
            )
        )
        messages.extend([agent_out, repair])
        route_msg = router_llm.invoke(messages)

    route = backup(route_msg)
    return {**state, "route": route}

# ========================= 6) Retrieval mapping =========================

ROUTE2FUNC = {
    "products": fetch_products,
    "orders":   fetch_orders,
    "faq":      fetch_faq,
    "none":     lambda _: {},
}

def build_context(state: AgentState) -> AgentState:
    fn = ROUTE2FUNC.get(state.get("route", "none"), ROUTE2FUNC["none"])
    ctx = fn(state["user_query"])
    # Attach profile hints to context to steer product filtering (budget/allergies)
    mem_profile = (state.get("memory") or {}).get("profile", {})
    if mem_profile:
        ctx = {**ctx, "_memory_profile": mem_profile}
    return {**state, "context": ctx}

# ========================= 7) Memory nodes =========================

def load_memory(state: AgentState) -> AgentState:
    user_id = state.get("user_id") or "anonymous"
    user_mem = MEMORY.get_user(user_id)
    # Append this user turn into transient history 
    hist = user_mem.get("history", [])
    # We push in save_memory after we have the agent reply
    return {**state, "memory": user_mem}

def save_memory(state: AgentState) -> AgentState:
    user_id = state.get("user_id") or "anonymous"
    user_mem = state.get("memory") or MEMORY.get_user(user_id)

    # 1) Extract profile facts from the latest user message
    facts = extract_facts_from_text(state["user_query"])

    # 2) Merge profile
    if facts.get("profile"):
        user_mem["profile"] = merge_profiles(user_mem.get("profile", {}), facts["profile"])

    # 3) Append the last turn to history
    history = user_mem.get("history", [])
    history.extend([
        {"role": "user", "text": state["user_query"]},
        {"role": "agent", "text": state.get("answer","")}
    ])
    user_mem["history"] = history

    MEMORY.save_user(user_id, user_mem)
    return state

# ========================= 8) Generation =========================

def _format_history_for_prompt(history: List[Dict[str, str]], max_pairs: int = 3) -> str:
    # take last pairs (user, agent)
    trimmed = history[-2*max_pairs:] if history else []
    lines = []
    for h in trimmed:
        who = "User" if h["role"] == "user" else "Agent"
        lines.append(f"{who}: {h['text']}")
    return "\n".join(lines)

def generate_node(state: AgentState) -> AgentState:
    """Generate a friendly, context-aware response for the user query, using memory."""
    mem = state.get("memory") or {}
    profile = mem.get("profile", {})
    history_txt = _format_history_for_prompt(mem.get("history", []), max_pairs=3)

    prompt = f"""
    You are AURA, a skincare consultation agent and customer support agent for the company Seoulight.
    You help customers find the best products on the website and inform them about store policies and questions when appropriate.

    # Recent conversation (most recent last)
    {history_txt if history_txt else "(no recent history)"}

    # Known user profile (from prior visits; treat as soft constraints)
    {json.dumps(profile, ensure_ascii=False, indent=2) if profile else "(no saved profile)"}

    CONVERSATION RULES:
    - **Do not introduce yourself again** if you've already spoken to the user in this conversation or session. 
    - Only start with a greeting phrase once per session. Otherwise DO NOT start your reply withg hey or hi.
    - Focus on recommending scincare and sound professional but friendly. 
    - Only ask clarifying questions if needed for *this* query.
    - If recommending products, use the context + profile (avoid allergens, respect budget).
    - Never invent products. Only use provided context.
    - Keep replies concise, friendly, and natural. Avoid filler phrases.

    Now write the best response.

    # Current user message
    {state['user_query']}
    """
    # Safely add context if available and route is relevant
    route = state.get("route", "none")
    context = state.get("context", {})

    if route != "none" and context:
        try:
            prompt += "\n# Retrieved Context\n" + json.dumps(context, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Warning] Could not serialize context: {e}")
    print('\n', "Prompt right before generation: \n")
    print(prompt)
    
    answer = gen_llm.invoke(prompt)

    recommended_ids: List[Any] = []
    ctx = state.get("context") or {}
    prods = ctx.get("products") if isinstance(ctx, dict) else None
    if isinstance(prods, list):
        recommended_ids = extract_recommended_ids_from_answer(answer, prods)

    return {**state, "answer": answer, "recommended_ids": recommended_ids}


# ========================= 9) Build graph =========================

graph_builder = StateGraph(AgentState)

graph_builder.add_node("load_memory", load_memory)
graph_builder.add_node("route_node", route_node)
graph_builder.add_node("build_context", build_context)
graph_builder.add_node("generate_node", generate_node)
graph_builder.add_node("save_memory", save_memory)

graph_builder.add_edge(START, "load_memory")
graph_builder.add_edge("load_memory", "route_node")
graph_builder.add_edge("route_node", "build_context")
graph_builder.add_edge("build_context", "generate_node")
graph_builder.add_edge("generate_node", "save_memory")
graph_builder.add_edge("save_memory", END)

app = graph_builder.compile()

# ========================= 10) Utilities =========================

def finalize_state(s: AgentState) -> AgentState:
    s.setdefault("route", "none")
    s.setdefault("context", {})
    s.setdefault("answer", "")
    s.setdefault("tool_calls", [])
    s.setdefault("warnings", [])
    s.setdefault("errors", [])
    s.setdefault("trace_id", "")
    s.setdefault("latency_ms", 0)
    s.setdefault("tokens", {})
    s.setdefault("memory", {})
    s.setdefault("recommended_ids", [])
    return s

def call_llm(query: str, user_id: Optional[str] = None) -> AgentState:
    final: AgentState = app.invoke({"user_query": query, "user_id": user_id or "anonymous"})
    return finalize_state(final)

def try_performance(user_id: Optional[str] = None):
    user_queries = [
        {"user_query": "Hi, how are you?", "expected": "none"},
        {"user_query": "Tell me a fun fact about skincare.", "expected": "none"},
        {"user_query": "What’s the weather like today?", "expected": "none"},
        {"user_query": "Do you like working with people?", "expected": "none"},
        {"user_query": "Which moisturizer is best for dry sensitive skin?", "expected": "products"},
        {"user_query": "Can you recommend a serum for oily skin?", "expected": "products"},
        {"user_query": "Can I track my last order?", "expected": "orders"},
        {"user_query": "How long does shipping usually take to Seoul?", "expected": "orders"},
        {"user_query": "What is your return policy?", "expected": "faq"},
        {"user_query": "Do you accept international payments?", "expected": "faq"},
    ]
    correct = 0
    for q in user_queries:
        out = app.invoke({"user_query": q["user_query"], "user_id": user_id or "anonymous"})
        predicted = out.get("route")
        is_correct = predicted == q["expected"]
        if is_correct:
            correct += 1
        print(f"User: {q['user_query']}")
        print("Final LangGraph State:", out)
        print(f"Predicted Router: {predicted} | Expected: {q['expected']} --> {'Correct' if is_correct else 'Incorrect'}\n")
    print(f"Total correct: {correct}/{len(user_queries)} ({(correct/len(user_queries))*100:.1f}%)")

if __name__ == "__main__":
    out = app.invoke({"user_query": "I want a fragrance-free moisturizer under ₩30k for dry sensitive skin", "user_id": "demo_user"})
    print("final langgraph:", out)
