import json
from pathlib import Path
import kagglehub
from kagglehub import KaggleDatasetAdapter
import re
from pathlib import Path

file_path = "productlist.csv"

# Load the latest version
df = kagglehub.load_dataset(
  KaggleDatasetAdapter.PANDAS,
  "taniadh/skin-care",
  file_path,
)

print("First 5 records:", df.head())
print(df.columns.to_list())

# Clean / fill NaN
df = df.fillna("")

def parse_price(price_str):
    """Extract numeric value and currency symbol."""
    if not isinstance(price_str, str):
        price_str = str(price_str)
    price_str = price_str.strip()
    if not price_str:
        return 0.0, ""
    # Match currency symbol and number (e.g. "$42.50" or "€19.90")
    match = re.match(r"([^\d]+)?\s*([\d.,]+)", price_str)
    if match:
        symbol = match.group(1).strip() if match.group(1) else ""
        number_str = match.group(2).replace(",", "")
        try:
            value = float(number_str)
        except ValueError:
            value = 0.0
        return value, symbol
    return 0.0, ""


products = []
for i, row in df.head(20).iterrows():
    price_value, currency_symbol = parse_price(row["price"])
    currency_code = (
        "USD" if currency_symbol == "$"
        else "EUR" if currency_symbol == "€"
        else ""
    )

    products.append({
        "id": int(row["product_ID"]) if "product_ID" in row else int(i) + 1,
        "title": str(row["product_name"]).strip(),
        "brand": str(row["product_brand"]).strip(),
        "price_value": price_value,
        "currency": currency_code,
        "price_display": f"{currency_symbol}{price_value}",
        "description": str(row["product_description"]).strip()[:400],
        "image": "",  # Add URLs or local paths later
        "category": str(row["product_type"]).strip(),
        "rating": None,
        "availability": "In stock"
    })

out_path = Path("data/products.json")
# Save to JSON file
with open(out_path, "w") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"Saved {len(products)} products to {out_path}")
