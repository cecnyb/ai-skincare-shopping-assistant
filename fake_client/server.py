from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
from pathlib import Path
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# --------------------------------
# Paths
# --------------------------------
# BASE_DIR = folder that contains server.py
BASE_DIR = Path(__file__).parent.resolve()

DATA_DIR = BASE_DIR / "data"

# --------------------------------
# Load data at startup
# --------------------------------
with open(DATA_DIR / "products.json") as f:
    PRODUCTS = json.load(f)

with open(DATA_DIR / "reviews.json") as f:
    REVIEWS = json.load(f)

with open(DATA_DIR / "orders.json") as f:
    ORDERS = json.load(f)

with open(DATA_DIR / "faq.json") as f:
    FAQ = json.load(f)

# --------------------------------
# API: products
# --------------------------------
try:
    from sentence_transformers import SentenceTransformer
    device = "cpu"
    EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2", device=device)

    USE_EMBEDDINGS = True
except Exception:
    EMBEDDER = None
    USE_EMBEDDINGS = False

def _prod_text(p: dict) -> str:
    # Build a searchable text field (title + description + tags)
    parts = [
        p.get("name", ""),
        p.get("description", ""),
        " ".join(p.get("tags", [])) if isinstance(p.get("tags"), list) else str(p.get("tags", "")),
        p.get("brand", ""),
        p.get("category", ""),
    ]
    return " ".join(s for s in parts if s).strip()

PRODUCT_TEXTS = [_prod_text(p) for p in PRODUCTS]

# Precompute product embeddings once
if USE_EMBEDDINGS:
    PRODUCT_EMB = np.vstack([EMBEDDER.encode(t, normalize_embeddings=True) for t in PRODUCT_TEXTS])
else:
    PRODUCT_EMB = None

def _keyword_score(query: str, text: str) -> float:
    """Tiny BM25-ish proxy: fraction of query tokens present in text."""
    q_tokens = [w for w in query.lower().split() if w]
    if not q_tokens:
        return 0.0
    t = text.lower()
    hits = sum(1 for w in q_tokens if w in t)
    return hits / len(q_tokens)

def _score_products(query: str, top_k: int = 5):
    # 2) Embedding similarity
    if USE_EMBEDDINGS:
        q_vec = EMBEDDER.encode(query, normalize_embeddings=True)
        sim = PRODUCT_EMB @ q_vec  # cosine because normalized
    else:
        sim = np.zeros(len(PRODUCTS), dtype=float)

    # 3) Keyword signal
    kw = np.array([_keyword_score(query, txt) for txt in PRODUCT_TEXTS], dtype=float)

    # 4) Optional business prior (e.g., popularity if present, else 0)
    pop = np.array([p.get("popularity", 0) for p in PRODUCTS], dtype=float)
    if pop.max() > 0:
        pop = pop / (pop.max() or 1.0)  # normalize 0..1
    else:
        pop = np.zeros_like(sim)

    score = 0.70 * sim + 0.25 * kw + 0.05 * pop
    idx = np.argsort(-score)[:top_k]
    return [PRODUCTS[i] for i in idx]

@app.get("/api/products/match")
def get_products_match(q: str = "", top_k: int = 5):
    """
    Hybrid search over products:
      - semantic (embeddings) + keyword + optional popularity prior
    """
    q = q.strip()
    if not q:
        # If no query return top_k by popularity/name
        default = sorted(PRODUCTS, key=lambda p: p.get("popularity", 0), reverse=True)[:top_k]
        return {"products": default}

    matches = _score_products(q, top_k=top_k)
    return {"products": matches}


@app.get("/api/products")
def list_products():
    return {"products": PRODUCTS}

@app.get("/api/products/{pid}")
def get_product(pid: int):
    for p in PRODUCTS:
        # NOTE: compare as str to be safe if p["id"] is a huge int
        if str(p["id"]) == str(pid):
            return {"product": p}
    return {"error": "not found"}

# --------------------------------
# API: reviews
# --------------------------------
@app.get("/api/reviews")
def get_reviews(product_id: int):
    product_reviews = [
        r for r in REVIEWS
        if str(r["product_id"]) == str(product_id)
    ]
    return {"reviews": product_reviews}

# --------------------------------
# API: track order
# --------------------------------
@app.get("/api/orders/{order_number}")
def track_order(order_number: str):
    for o in ORDERS:
        if str(o["order_number"]) == str(order_number):
            return {"order": o}
    return {"error": "not found"}

# --------------------------------
# API: faq
# --------------------------------
@app.get("/api/faq")
def get_faq():
    return JSONResponse(FAQ)

# --------------------------------
# Frontend pages
# --------------------------------
@app.get("/")
def serve_index():
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/faq")
def serve_faq_page():
    return FileResponse(str(BASE_DIR / "faq.html"))

@app.get("/faq.html")
def serve_faq_page_compat():
    return FileResponse(str(BASE_DIR / "faq.html"))

@app.get("/index.html")
def serve_index_compat():
    return FileResponse(str(BASE_DIR / "index.html"))
