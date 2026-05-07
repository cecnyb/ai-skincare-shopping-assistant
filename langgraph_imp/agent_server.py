from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import logging
from langchain_agent import call_llm, AgentState  # Import the agent

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agent")

agent_app = FastAPI()
agent_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str = Field(..., description="User's natural language query")
    context: Optional[Dict[str, Any]] = None

class AskResponse(BaseModel):
    api_version: str = "2025-11-05"
    status: str
    message: str = ""
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None 
    route: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    

@agent_app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, x_user_id: str = Header(default="anonymous")) -> AskResponse:
    user_q = (req.question or "").strip()
    user_id = x_user_id 
    if not user_q:
        return AskResponse(
            status="error",
            message="Please provide a non-empty question.",
            route="none",
        )
    try:
        state: AgentState = call_llm(user_q, user_id)  # internal result 
        print("state", state)
        response =  AskResponse(
            status="error" if state.get("errors") else "ok",
            message=state.get("answer", ""),
            route=state.get("route"),
            data=state.get("context") or None,
            tool_calls=state.get("tool_calls", []),
            meta={
                "trace_id": state.get("trace_id", ""),
                "latency_ms": state.get("latency_ms", 0),
                "tokens": state.get("tokens", {}),
                "recommended_ids": state.get("recommended_ids", []), 
            },
        )

        return response
    except Exception as e:
        log.exception("Agent failed")
        return AskResponse(
            status="error",
            message=f"Sorry, something went wrong on my side ({e}).",
            route="none",
        )

@agent_app.get("/health")
def health():
    return {"ok": True, "msg": "agent running"}
