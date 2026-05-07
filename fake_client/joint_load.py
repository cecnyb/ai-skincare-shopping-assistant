import pandas as pd
import json
import re
from pathlib import Path
import kagglehub
from kagglehub import KaggleDatasetAdapter

# -------------------------------------------------
# 1. Load both datasets
# -------------------------------------------------

products_df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "taniadh/skin-care",
    "productlist.csv",
)
reviews_df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "taniadh/skin-care",
    "productReviews.csv",
)

products_df = products_df.fillna("")
reviews_df = reviews_df.fillna("")

print("products columns:", products_df.columns.tolist())
print("reviews columns:", reviews_df.columns.tolist())

# Expect:
# products_df columns ~ ['product_ID', 'product_name', 'product_brand', 'price', 'product_description', 'product_type', ...]
# reviews_df columns ~ ['product_id', 'review']


# -------------------------------------------------
# 2. Normalize IDs (make sure they're comparable)
# -------------------------------------------------

def to_int_safe(x):
    try:
        return int(str(x).strip())
    except Exception:
        return None

products_df["pid"] = products_df["product_ID"].apply(to_int_safe)
reviews_df["pid"] = reviews_df["product_id"].apply(to_int_safe)

# Build lookup: pid -> product row dict
product_lookup = {}
for _, prow in products_df.iterrows():
    pid = prow["pid"]
    if pid is None:
        continue
    product_lookup[pid] = prow  # store the whole row for now

# Build lookup: pid -> list of review strings
review_lookup = {}
for _, rrow in reviews_df.iterrows():
    pid = rrow["pid"]
    if pid is None:
        continue
    txt = str(rrow["review"]).strip()
    if not txt:
        continue
    review_lookup.setdefault(pid, []).append(txt)

# -------------------------------------------------
# 3. Find the intersection: products that also have reviews
# -------------------------------------------------

intersection_pids = [pid for pid in review_lookup.keys() if pid in product_lookup]

print("Number of product IDs with both product info AND reviews:", len(intersection_pids))

# We'll now build a small demo set: take first 20 product IDs from that intersection
demo_pids = intersection_pids[:20]

# -------------------------------------------------
# 4. Price parsing helpers
# -------------------------------------------------

def parse_price(price_str):
    """Extract numeric value and currency symbol for '$42.50', '€19', etc."""
    if not isinstance(price_str, str):
        price_str = str(price_str)
    s = price_str.strip()
    if not s:
        return 0.0, ""
    m = re.match(r"([^\d]+)?\s*([\d.,]+)", s)
    if m:
        symbol = m.group(1).strip() if m.group(1) else ""
        number_str = m.group(2).replace(",", "")
        try:
            value = float(number_str)
        except ValueError:
            value = 0.0
        return value, symbol
    return 0.0, ""

def symbol_to_currency_code(symbol: str) -> str:
    if symbol == "$":
        return "USD"
    if symbol == "€":
        return "EUR"
    if symbol == "£":
        return "GBP"
    return ""

#Use mock images based on category keywords since we don't have real images in the dataset. This is just for demo purposes.
IMAGE_MAP = {
    "serum": "https://plus.unsplash.com/premium_photo-1674739375749-7efe56fc8bbb?auto=format&fit=crop&q=80&w=400",
    "cream": "https://images.unsplash.com/photo-1608068811588-3a67006b7489?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8Y3JlYW18ZW58MHx8MHx8fDA%3D&auto=format&fit=crop&q=60&w=500",
    "moisturizer": "https://images.unsplash.com/photo-1556229162-5c63ed9c4efb?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTR8fG1vaXN0dXJpemVyfGVufDB8fDB8fHww&auto=format&fit=crop&q=60&w=500",
    "cleanser": "https://images.unsplash.com/photo-1556229010-aa3f7ff66b24?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fGNsZWFuc2VyfGVufDB8fDB8fHww&auto=format&fit=crop&q=60&w=500",
    "toner": "https://images.unsplash.com/photo-1616986953793-2e6159b78580?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8dG9uZXJ8ZW58MHx8MHx8fDA%3D&auto=format&fit=crop&q=60&w=500",
    "essence": "https://plus.unsplash.com/premium_photo-1675018082227-b9daac6483dc?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8RXNzZW5jZXxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&q=60&w=500",
    "sunscreen": "https://plus.unsplash.com/premium_photo-1682535210542-21dceae4530c?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8c3VuJTIwc2NyZWVufGVufDB8fDB8fHww&auto=format&fit=crop&q=60&w=500",
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1559881230-1af605ca3f67?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MjB8fHNraW4lMjBjYXJlfGVufDB8fDB8fHww&auto=format&fit=crop&q=60&w=500"

def pick_image_for_product(category: str) -> str:
    """
    Pick an image based on the product category value.
    Falls back to DEFAULT_IMAGE if no match found.
    """
    if not category:
        return DEFAULT_IMAGE

    cat = category.strip().lower()

    # try exact or partial matches
    if "serum" in cat:
        return IMAGE_MAP["serum"]
    elif "essence" in cat:
        return IMAGE_MAP["essence"]
    elif "toner" in cat:
        return IMAGE_MAP["toner"]
    elif "cleanser" in cat or "wash" in cat or "foam" in cat:
        return IMAGE_MAP["cleanser"]
    elif "sunscreen" in cat or "spf" in cat or "sun protection" in cat:
        return IMAGE_MAP["sunscreen"]
    elif "moisturizer" in cat or "moisturiser" in cat:
        return IMAGE_MAP["moisturizer"]
    elif "cream" in cat or "lotion" in cat or "balm" in cat:
        return IMAGE_MAP["cream"]
    else:
        return DEFAULT_IMAGE

# -------------------------------------------------
# 5. Build final products.json
# -------------------------------------------------

final_products = []

for pid in demo_pids:
    prow = product_lookup[pid]

    price_value, currency_symbol = parse_price(prow.get("price", ""))

    name_str = str(prow.get("product_name", "")).strip()
    type_str = str(prow.get("product_type", "")).strip()
    product_image = pick_image_for_product(type_str)

    final_products.append({
        "id": pid,
        "title": name_str,
        "brand": str(prow.get("product_brand", "")).strip(),
        "price_value": price_value,
        "currency": symbol_to_currency_code(currency_symbol),
        "price_display": f"{currency_symbol}{price_value}" if currency_symbol else str(price_value),
        "description": str(prow.get("product_description", "")).strip(),
        "image": product_image,
        "category": type_str,
        "rating": None,
        "availability": "In stock",
    })

# -------------------------------------------------
# 6. Build final reviews.json
#    We'll include up to 3 reviews per product to keep it clean.
# -------------------------------------------------

final_reviews = []
for pid in demo_pids:
    product_reviews = review_lookup.get(pid, [])
    take = product_reviews[:3]  # cap at 3 per product
    for txt in take:
        final_reviews.append({
            "product_id": pid,
            "text": txt,
        })

# -------------------------------------------------
# 7. Save to disk
# -------------------------------------------------

data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)

products_out = data_dir / "products.json"
reviews_out = data_dir / "reviews.json"

with open(products_out, "w") as f:
    json.dump(final_products, f, indent=2, ensure_ascii=False)

with open(reviews_out, "w") as f:
    json.dump(final_reviews, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(final_products)} products to {products_out}")
print(f"Wrote {len(final_reviews)} reviews to {reviews_out}")
print("Sample product IDs in demo set:", demo_pids)
