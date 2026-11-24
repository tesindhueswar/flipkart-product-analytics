import pandas as pd
df = pd.read_csv("flipkart_com-ecommerce_sample.csv")
tree = df["product_category_tree"].astype(str).str.strip('["]').str.split(" >> ")
has = tree.apply(len) > 1
brand = df["brand"].fillna("Unknown")
out = pd.DataFrame({
    "product_id": range(1, len(df) + 1),
    "product_name": df["product_name"],
    "category": [t[0] if h else "Other" for t, h in zip(tree, has)],
    "sub_category": [t[1] if h else "Other" for t, h in zip(tree, has)],
    "brand": brand,
    "retail_price": df["retail_price"],
    "discount_price": df["discounted_price"],
    "rating": pd.to_numeric(df["product_rating"], errors="coerce"),
    "num_reviews": pd.NA,
    "seller_name": brand,
    "stock_status": "Unknown",
    "product_url": df["product_url"],
})
out = out.drop_duplicates(subset=["product_name", "retail_price", "discount_price"]).reset_index(drop=True)
out["product_id"] = range(1, len(out) + 1)
out.to_csv("flipkart_converted.csv", index=False)
print(out.shape, out["category"].nunique(), "categories")
print(out["category"].value_counts().head(5))
