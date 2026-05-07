import re
import requests
from typing import List, Dict, Any

STORE_API_BASE = "http://localhost:8002"
############################
# 1. Helpers to talk to store
############################

def fetch_faq(query: str = "") -> Dict[str, Any]:
    """GET /api/faq from the storefront backend."""
    r = requests.get(f"{STORE_API_BASE}/api/faq", timeout=5)
    r.raise_for_status()
    items = r.json()
    # normalize to dict
    if isinstance(items, list):
        return {"faq": items}
    if isinstance(items, dict):
        # backend might already return {"faq": [...]}
        return items
    return {"faq": [items]}  

def first_two_sentences(text: str) -> str:
    if not text:
        return ""
    # Split on period + space OR end of line
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:2])  # take first two


def fetch_products(query: str = "") -> dict:
    """GET /api/products from the storefront backend, limited to top 5 results."""
    r = requests.get(
        f"{STORE_API_BASE}/api/products/match",
        params={"q": query, "top_k": 5},
        timeout=5,
    )
    r.raise_for_status()
    data = r.json()

    # Normalize the structure
    if isinstance(data, list):
        prods = data[:5]
        for p in prods:
            if "description" in p:
                p["description"] = first_two_sentences(p["description"])
        return {"products": prods}

    if isinstance(data, dict) and "products" in data:
        data["products"] = data["products"][:5]
        for p in data["products"]:
            if "description" in p:
                p["description"] = first_two_sentences(p["description"])
        return data

    return data


def fetch_orders(query: str = "") -> Dict[str, Any]:
    """Not implemented at this time."""
    return {"orders": [{"id": None, "status": "Unknown"}]}#{"orders": [{"id": 101, "status": "in transit"}]}

def fetch_none(query: str = "") -> Dict[str, Any]:
    """Fallback for no retrieval."""
    return {}


def fetch_reviews(product_id: int, top_k: int = 5) -> dict:
    r = requests.get(
        f"{STORE_API_BASE}/api/reviews",
        params={"product_id": product_id, "top_k": top_k},
        timeout=5,
    )
    r.raise_for_status()
    return {"reviews": r.json()}


def fetch_reviews_for_query(query: str) -> dict:
    products = fetch_products(query)
    reviews = []
    for p in products.get("products", [])[:3]:
        pid = p.get("id")
        if pid:
            reviews.extend(fetch_reviews(product_id=pid).get("reviews", []))
    return {"reviews": reviews}


