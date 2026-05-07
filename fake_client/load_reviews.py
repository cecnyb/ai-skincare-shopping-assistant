import pandas as pd
import json
from pathlib import Path
import kagglehub
from kagglehub import KaggleDatasetAdapter
import re
from pathlib import Path

file_path = "productReviews.csv"

df = kagglehub.load_dataset(
  KaggleDatasetAdapter.PANDAS,
  "taniadh/skin-care",
  file_path,
)

print("First 5 records:", df.head())
print(df.columns.to_list())

products_json = Path("data/products.json")
out_path = Path("data/reviews.json")

# Clean / fill NaN
df = df.fillna("")

#'product_id', 'review'
products = []
for i, row in df.head(20).iterrows():

    products.append({
        "product_id": int(row["product_id"]) if "product_id" in row else int(i) + 1,
        "text": str(row["review"]).strip(),
    })

out_path = Path("data/reviews.json")
# Save to JSON file
with open(out_path, "w") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"Saved {len(products)} products to {out_path}")
