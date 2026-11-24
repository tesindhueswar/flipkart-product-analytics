"""Creates a messy SAMPLE Flipkart 'other products' CSV (only used if you don't have the real file)."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
tree = {
 "Electronics": ["Mobiles", "Headphones", "Laptops", "Cameras", "Smart Watches"],
 "Clothing": ["Men Tshirts", "Women Kurtas", "Jeans", "Sarees", "Kids Wear"],
 "Home & Kitchen": ["Cookware", "Furniture", "Home Decor", "Bedsheets", "Storage"],
 "Beauty": ["Skincare", "Makeup", "Haircare", "Fragrances"],
 "Sports": ["Cricket", "Fitness", "Footwear", "Yoga"],
 "Books": ["Fiction", "Academic", "Comics"],
}
brands = ["Samsung","boAt","Realme","Puma","Nike","Prestige","Wildcraft","Lakme","Maybelline","Allen Solly",
          "Biba","W","Levis","Philips","Sony","Milton","Cello","Nivia","SG","Penguin","HP","Lenovo","Noise","Mamaearth"]
sellers = ["RetailNet","SuperComNet","BestDeals","OmniTech","StarSellers","TrendyHub","Flash Mart","UrbanCart",
           "PrimeTraders","HomeEssentials","GadgetWorld","StyleBazaar"]
n = 6000
rows = []
for i in range(1, n + 1):
    cat = rng.choice(list(tree)); sub = rng.choice(tree[cat])
    base = {"Electronics":9000,"Clothing":900,"Home & Kitchen":1500,"Beauty":500,"Sports":1200,"Books":350}[cat]
    retail = round(float(rng.lognormal(np.log(base), 0.6)), 0)
    disc_pct = float(rng.choice([0,5,10,15,20,30,40,50,60,70], p=[.05,.08,.12,.15,.15,.15,.12,.1,.05,.03]))
    dprice = round(retail * (1 - disc_pct/100), 0)
    rating = round(float(np.clip(rng.normal(3.9, 0.7), 1, 5)), 1)
    rows.append(dict(product_id=i, product_name=f"{rng.choice(brands)} {sub} Item {i}", category=cat, subcategory=sub,
        brand=rng.choice(brands), retail_price=retail, discounted_price=dprice, rating=rating,
        review_count=int(rng.integers(0, 20000) * (rating/5)), seller=rng.choice(sellers),
        stock_status=rng.choice(["In stock","Out of stock","Limited stock"], p=[.7,.15,.15]),
        product_url=f"https://www.flipkart.com/p/item{i}"))
df = pd.DataFrame(rows)
# ---- inject mess ----
df["retail_price"] = df["retail_price"].astype(object)
df.loc[df.sample(frac=.05, random_state=1).index, "retail_price"] = np.nan
df.loc[df.sample(frac=.04, random_state=2).index, "rating"] = np.nan
df.loc[df.sample(frac=.03, random_state=3).index, "discounted_price"] = np.nan
fmt = df.sample(frac=.05, random_state=4).index
df.loc[fmt, "retail_price"] = df.loc[fmt, "retail_price"].apply(lambda x: f"Rs. {x:,.0f}" if pd.notna(x) else x)
df.loc[df.sample(n=15, random_state=5).index, "rating"] = 7.5          # invalid rating
df.loc[df.sample(n=10, random_state=6).index, "review_count"] = -5     # negative reviews
df.loc[df.sample(n=8, random_state=7).index, "retail_price"] = -100    # invalid price
messy = df.sample(frac=.08, random_state=8).index
df.loc[messy, "stock_status"] = df.loc[messy, "stock_status"].str.upper()
df.loc[df.sample(frac=.03, random_state=9).index, "brand"] = "  " + df["brand"] + " "
df.loc[df.sample(frac=.03, random_state=10).index, "stock_status"] = "instock"
df = pd.concat([df, df.sample(120, random_state=11)], ignore_index=True)  # duplicates
df.to_csv("data/other_products_raw.csv", index=False)
print(df.shape)
