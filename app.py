"""
Flipkart Product Analytics Dashboard
Run:  streamlit run app.py
Pages: Dashboard | Data Explorer | Analysis | CRUD Operations | SQL Query Explorer
"""
import os
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Flipkart Analytics", page_icon="🛒", layout="wide")

# --------------------------------------------------------------------------
# Database connection  (edit the defaults or set environment variables)
# --------------------------------------------------------------------------
DB = dict(
    user=os.getenv("FLIPKART_DB_USER", "root"),
    password=os.getenv("FLIPKART_DB_PASSWORD", "your_password"),  # <-- change me
    host=os.getenv("FLIPKART_DB_HOST", "localhost"),
    port=os.getenv("FLIPKART_DB_PORT", "3306"),
    name=os.getenv("FLIPKART_DB_NAME", "flipkart_db"),
)
MAIN = "flipkart_other_products"
SQL_FILE = Path(__file__).parent / "sql" / "03_business_queries.sql"


@st.cache_resource
def get_engine():
    # URL.create escapes special characters (@ : / # ...) in the password safely
    url = URL.create("mysql+pymysql", username=DB["user"], password=DB["password"],
                     host=DB["host"], port=int(DB["port"]), database=DB["name"])
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


@st.cache_data(ttl=60, show_spinner=False)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as con:
        return pd.read_sql(text(sql), con, params=params or {})


def execute(sql: str, params: dict | None = None):
    """Write statement (INSERT / UPDATE / DELETE) in its own transaction."""
    with get_engine().begin() as con:
        con.execute(text(sql), params or {})


# --- small helpers so the app works on old and new Streamlit versions -------
def show_chart(fig):
    fig.update_layout(margin=dict(l=10, r=10, t=45, b=10))
    try:
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.plotly_chart(fig, use_container_width=True)


def show_df(df, **kw):
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


def csv_button(df, name, label="⬇️ Download CSV", key=None):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=name, mime="text/csv", key=key)


# --------------------------------------------------------------------------
# Connection check
# --------------------------------------------------------------------------
try:
    run_query(f"SELECT 1 FROM {MAIN} LIMIT 1")
except Exception as e:  # noqa: BLE001
    st.error("❌ Could not connect to MySQL or the tables are missing.")
    st.code(str(e)[:500])
    st.info("1) Start MySQL  2) run the notebook to create/load the tables  "
            "3) set FLIPKART_DB_PASSWORD (or edit the DB dict at the top of app.py).")
    st.stop()

# --------------------------------------------------------------------------
# Sidebar: navigation + global filters
# --------------------------------------------------------------------------
with st.sidebar:
    page = option_menu(
        "🛒 Flipkart Analytics",
        ["Dashboard", "Data Explorer", "Analysis", "CRUD Operations", "SQL Query Explorer"],
        icons=["speedometer2", "table", "bar-chart-line", "pencil-square", "database"],
        default_index=0,
    )

FILTER_PAGES = {"Dashboard", "Data Explorer", "Analysis"}


def distinct(col, where="", params=None):
    df = run_query(f"SELECT DISTINCT {col} FROM {MAIN} {where} ORDER BY {col}", params)
    return df[col].dropna().tolist()


def sidebar_filters():
    """Renders the global filters and returns (where_sql, params)."""
    st.sidebar.markdown("### 🔎 Filters")
    cats = st.sidebar.multiselect("Category", distinct("category"))
    if cats:
        ph = ",".join(f":c{i}" for i in range(len(cats)))
        subs_all = distinct("sub_category", f"WHERE category IN ({ph})", {f"c{i}": v for i, v in enumerate(cats)})
    else:
        subs_all = distinct("sub_category")
    subs = st.sidebar.multiselect("Sub-category", subs_all)
    brands = st.sidebar.multiselect("Brand", distinct("brand"))
    sellers = st.sidebar.multiselect("Seller", distinct("seller_name"))
    stocks = st.sidebar.multiselect("Stock status", distinct("stock_status"))

    lim = run_query(f"SELECT MIN(retail_price) lo, MAX(retail_price) hi, MAX(discount_percentage) dmax FROM {MAIN}").iloc[0]
    rating = st.sidebar.slider("Rating", 0.0, 5.0, (0.0, 5.0), 0.1)
    price = st.sidebar.slider("Retail price (₹)", 0, int(lim.hi) + 1, (0, int(lim.hi) + 1))
    disc = st.sidebar.slider("Discount %", 0, 100, (0, 100))

    clauses, params = ["rating BETWEEN :r_lo AND :r_hi",
                       "retail_price BETWEEN :p_lo AND :p_hi",
                       "discount_percentage BETWEEN :d_lo AND :d_hi"], {
        "r_lo": rating[0], "r_hi": rating[1], "p_lo": price[0], "p_hi": price[1], "d_lo": disc[0], "d_hi": disc[1]}
    for col, vals, tag in [("category", cats, "cat"), ("sub_category", subs, "sub"), ("brand", brands, "br"),
                           ("seller_name", sellers, "sel"), ("stock_status", stocks, "st")]:
        if vals:
            ph = ",".join(f":{tag}{i}" for i in range(len(vals)))
            clauses.append(f"{col} IN ({ph})")
            params.update({f"{tag}{i}": v for i, v in enumerate(vals)})
    return "WHERE " + " AND ".join(clauses), params


where, params = sidebar_filters() if page in FILTER_PAGES else ("", {})


def Q(select_sql: str) -> pd.DataFrame:
    """Run a query on the filtered main table. Use {W} where the WHERE clause goes."""
    return run_query(select_sql.replace("{W}", where), params)


# ==========================================================================
# PAGE 1 - DASHBOARD
# ==========================================================================
if page == "Dashboard":
    st.title("📊 Flipkart Product Dashboard")
    k = Q(f"""SELECT COUNT(*) n, ROUND(AVG(rating),2) r, ROUND(AVG(discount_percentage),1) d,
                     ROUND(AVG(retail_price),0) p, SUM(num_reviews) rev, COUNT(DISTINCT seller_name) s,
                     COUNT(DISTINCT brand) b FROM {MAIN} {{W}}""").iloc[0]
    if not k.n:
        st.warning("No products match the current filters.")
        st.stop()
    cols = st.columns(6)
    for c, (label, val) in zip(cols, [("Total products", f"{int(k.n):,}"), ("Avg rating", f"{k.r} ⭐"),
                                      ("Avg discount", f"{k.d}%"), ("Avg retail price", f"₹{int(k.p):,}"),
                                      ("Total reviews", f"{int(k.rev):,}"), ("Sellers / Brands", f"{int(k.s)} / {int(k.b)}")]):
        with c.container(border=True):
            st.metric(label, val)

    c1, c2 = st.columns(2)
    d = Q(f"SELECT category, COUNT(*) products FROM {MAIN} {{W}} GROUP BY category ORDER BY products DESC")
    show_chart(px.bar(d, x="category", y="products", color="category", title="Products by category", text_auto=True)
               .update_layout(showlegend=False))
    with c1:
        d = Q(f"SELECT stock_status, COUNT(*) products FROM {MAIN} {{W}} GROUP BY stock_status")
        show_chart(px.pie(d, names="stock_status", values="products", hole=.5, title="Stock status"))
    with c2:
        d = Q(f"SELECT rating_category, COUNT(*) products FROM {MAIN} {{W}} GROUP BY rating_category")
        show_chart(px.pie(d, names="rating_category", values="products", hole=.5, title="Rating category"))

    st.subheader("💡 Key business insights (live)")
    cat = Q(f"SELECT category, COUNT(*) n, AVG(discount_percentage) d, AVG(rating) r FROM {MAIN} {{W}} GROUP BY category")
    sel = Q(f"SELECT seller_name, COUNT(*) n, AVG(rating) r FROM {MAIN} {{W}} GROUP BY seller_name")
    sel = sel[sel.seller_name != "Unknown"]
    stock = Q(f"SELECT 100*SUM(stock_status='Out of stock')/COUNT(*) AS oos FROM {MAIN} {{W}}").iloc[0, 0]
    hi = Q(f"SELECT 100*SUM(discount_percentage>30)/COUNT(*) AS hi FROM {MAIN} {{W}}").iloc[0, 0]
    st.markdown(
        f"- **{cat.loc[cat.n.idxmax(), 'category']}** is the largest category ({int(cat.n.max()):,} listings).\n"
        f"- **{cat.loc[cat.d.idxmax(), 'category']}** gives the deepest average discount ({cat.d.max():.1f}%).\n"
        f"- **{cat.loc[cat.r.idxmax(), 'category']}** has the best average rating ({cat.r.max():.2f}).\n"
        f"- **{sel.loc[sel.n.idxmax(), 'seller_name']}** has the most listings; **{sel.loc[sel.r.idxmax(), 'seller_name']}** has the best average rating.\n"
        f"- {hi:.0f}% of listings are discounted by more than 30%, and {stock:.0f}% are out of stock."
    )

# ==========================================================================
# PAGE 2 - DATA EXPLORER
# ==========================================================================
elif page == "Data Explorer":
    st.title("🔍 Data Explorer")
    search = st.text_input("Search product name")
    sql = f"SELECT * FROM {MAIN} {where}"
    p = dict(params)
    if search:
        sql += " AND product_name LIKE :s"
        p["s"] = f"%{search}%"
    sql += " ORDER BY product_id"
    data = run_query(sql, p)
    st.caption(f"{len(data):,} products match the filters")
    show_df(data.head(5000))
    if len(data) > 5000:
        st.info("Showing the first 5,000 rows. The download contains all filtered rows.")
    csv_button(data, "filtered_products.csv")

# ==========================================================================
# PAGE 3 - ANALYSIS (product, category, brand, pricing, discount, seller)
# ==========================================================================
elif page == "Analysis":
    st.title("📈 Analysis")
    tabs = st.tabs(["Product", "Category", "Brand", "Pricing", "Discount", "Seller"])

    with tabs[0]:
        a, b = st.columns(2)
        with a:
            st.markdown("**Top-rated products** (min. 100 reviews)")
            show_df(Q(f"""SELECT product_name, brand, rating, num_reviews FROM {MAIN} {{W}}
                          AND num_reviews >= 100 ORDER BY rating DESC, num_reviews DESC LIMIT 10"""))
        with b:
            st.markdown("**Most reviewed products**")
            show_df(Q(f"SELECT product_name, brand, rating, num_reviews FROM {MAIN} {{W}} ORDER BY num_reviews DESC LIMIT 10"))
        d = Q(f"SELECT rating, num_reviews, category FROM {MAIN} {{W}} ORDER BY RAND() LIMIT 2000")
        show_chart(px.scatter(d, x="rating", y="num_reviews", color="category", opacity=.6, title="Rating vs review count (sample of 2,000)"))
        d = Q(f"SELECT rating_category, COUNT(*) products FROM {MAIN} {{W}} GROUP BY rating_category")
        show_chart(px.bar(d, x="rating_category", y="products", title="Products by rating category", text_auto=True))

    with tabs[1]:
        d = Q(f"SELECT category, sub_category, COUNT(*) products FROM {MAIN} {{W}} GROUP BY category, sub_category")
        show_chart(px.treemap(d, path=["category", "sub_category"], values="products", title="Products by category / sub-category"))
        d = Q(f"SELECT category, ROUND(AVG(rating),2) avg_rating, COUNT(*) products FROM {MAIN} {{W}} GROUP BY category ORDER BY avg_rating DESC")
        show_chart(px.bar(d, x="category", y="avg_rating", text_auto=True, title="Average rating by category"))
        show_df(d)

    with tabs[2]:
        n = st.slider("Number of brands", 5, 30, 10)
        d = Q(f"SELECT brand, COUNT(*) products, ROUND(AVG(rating),2) avg_rating, ROUND(AVG(discount_percentage),1) avg_discount "
              f"FROM {MAIN} {{W}} GROUP BY brand ORDER BY products DESC LIMIT {int(n)}")
        show_chart(px.bar(d, x="products", y="brand", orientation="h", title=f"Top {n} brands by listings").update_yaxes(autorange="reversed"))
        show_df(d)

    with tabs[3]:
        d = Q(f"SELECT category, ROUND(AVG(retail_price),0) AS avg_retail, ROUND(AVG(discount_price),0) AS avg_discount_price "
              f"FROM {MAIN} {{W}} GROUP BY category").melt("category", var_name="type", value_name="price")
        show_chart(px.bar(d, x="category", y="price", color="type", barmode="group", title="Average retail vs discount price"))
        d = Q(f"SELECT retail_price FROM {MAIN} {{W}} AND retail_price < 50000")
        show_chart(px.histogram(d, x="retail_price", nbins=60, title="Retail price distribution (< ₹50,000)"))

    with tabs[4]:
        a, b = st.columns(2)
        with a:
            d = Q(f"SELECT category, ROUND(AVG(discount_percentage),2) avg_discount FROM {MAIN} {{W}} GROUP BY category ORDER BY avg_discount DESC")
            show_chart(px.bar(d, x="category", y="avg_discount", text_auto=True, title="Average discount % by category"))
        with b:
            d = Q(f"SELECT discount_range, COUNT(*) products FROM {MAIN} {{W}} GROUP BY discount_range")
            show_chart(px.pie(d, names="discount_range", values="products", hole=.45, title="Discount range distribution"))
        st.markdown("**Top 10 products by discount amount**")
        show_df(Q(f"SELECT product_name, brand, retail_price, discount_price, discount_amount, discount_percentage "
                  f"FROM {MAIN} {{W}} ORDER BY discount_amount DESC LIMIT 10"))

    with tabs[5]:
        d = Q(f"""SELECT seller_name, COUNT(*) listings, ROUND(AVG(rating),2) avg_rating, SUM(num_reviews) total_reviews,
                         ROUND(AVG(discount_percentage),1) avg_discount FROM {MAIN} {{W}} GROUP BY seller_name ORDER BY listings DESC""")
        d = d[d.seller_name != "Unknown"]
        d15 = d.head(15)
        a, b = st.columns(2)
        with a:
            show_chart(px.bar(d15, x="seller_name", y="listings", title="Listings per seller"))
        with b:
            show_chart(px.bar(d15.sort_values("avg_rating", ascending=False), x="seller_name", y="avg_rating", title="Average rating per seller"))
        show_chart(px.bar(d15.sort_values("avg_discount", ascending=False), x="seller_name", y="avg_discount", title="Average discount % per seller"))
        s = Q(f"SELECT seller_name, stock_status, COUNT(*) listings FROM {MAIN} {{W}} GROUP BY seller_name, stock_status")
        s = s[s.seller_name.isin(d15.seller_name)]
        show_chart(px.bar(s, x="seller_name", y="listings", color="stock_status", title="Stock status by seller"))
        st.markdown("**Seller performance table**")
        show_df(d)
        csv_button(d, "seller_performance.csv", key="seller_csv")

# ==========================================================================
# PAGE 4 - CRUD OPERATIONS
# ==========================================================================
elif page == "CRUD Operations":
    st.title("🛠️ CRUD Operations")
    st.caption("Changes are written to all three tables: flipkart_other_products, category_catalog and seller_performance.")

    def derived(retail, disc_price, rating):
        amt = round(retail - disc_price, 2)
        pct = round(amt / retail * 100, 2) if retail else 0.0
        cat = "Excellent" if rating >= 4 else "Good" if rating >= 3 else "Average"
        rng = "0-10%" if pct <= 10 else "10-30%" if pct <= 30 else "30-50%" if pct <= 50 else "50%+"
        return amt, pct, cat, rng

    def write_product(row: dict, new: bool):
        """Insert or update a product in the three tables inside one transaction."""
        with get_engine().begin() as con:
            if new:
                con.execute(text(f"""INSERT INTO {MAIN} (product_id, product_name, category, sub_category, brand, retail_price,
                    discount_price, discount_percentage, discount_amount, price_difference, rating, num_reviews, seller_name,
                    stock_status, rating_category, discount_range) VALUES (:product_id,:product_name,:category,:sub_category,:brand,
                    :retail_price,:discount_price,:discount_percentage,:discount_amount,:price_difference,:rating,:num_reviews,
                    :seller_name,:stock_status,:rating_category,:discount_range)"""), row)
                con.execute(text("""INSERT INTO category_catalog (product_id, product_name, brand, retail_price, discount_price,
                    discount_percentage, discount_amount, rating, num_reviews, product_url) VALUES (:product_id,:product_name,:brand,
                    :retail_price,:discount_price,:discount_percentage,:discount_amount,:rating,:num_reviews,:product_url)"""), row)
                con.execute(text("""INSERT INTO seller_performance (product_id, product_name, rating, num_reviews, stock_status,
                    rating_category, seller_name) VALUES (:product_id,:product_name,:rating,:num_reviews,:stock_status,
                    :rating_category,:seller_name)"""), row)
            else:
                con.execute(text(f"""UPDATE {MAIN} SET product_name=:product_name, category=:category, sub_category=:sub_category,
                    brand=:brand, retail_price=:retail_price, discount_price=:discount_price, discount_percentage=:discount_percentage,
                    discount_amount=:discount_amount, price_difference=:price_difference, rating=:rating, num_reviews=:num_reviews,
                    seller_name=:seller_name, stock_status=:stock_status, rating_category=:rating_category,
                    discount_range=:discount_range WHERE product_id=:product_id"""), row)
                con.execute(text("""UPDATE category_catalog SET product_name=:product_name, brand=:brand, retail_price=:retail_price,
                    discount_price=:discount_price, discount_percentage=:discount_percentage, discount_amount=:discount_amount,
                    rating=:rating, num_reviews=:num_reviews, product_url=:product_url WHERE product_id=:product_id"""), row)
                con.execute(text("""UPDATE seller_performance SET product_name=:product_name, rating=:rating, num_reviews=:num_reviews,
                    stock_status=:stock_status, rating_category=:rating_category, seller_name=:seller_name
                    WHERE product_id=:product_id"""), row)
        st.cache_data.clear()

    STOCK = ["In stock", "Limited stock", "Out of stock"]

    def product_form(prefix, d=None, new=True):
        d = d or {}
        c1, c2 = st.columns(2)
        pid = c1.number_input("Product ID", min_value=1, step=1, disabled=not new, key=f"{prefix}_id",
                              value=int(d.get("product_id", run_query(f"SELECT COALESCE(MAX(product_id),0)+1 n FROM {MAIN}").iloc[0, 0])))
        name = c2.text_input("Product name", d.get("product_name", ""), key=f"{prefix}_name")
        c1, c2, c3 = st.columns(3)
        cat = c1.text_input("Category", d.get("category", ""), key=f"{prefix}_cat")
        sub = c2.text_input("Sub-category", d.get("sub_category", ""), key=f"{prefix}_sub")
        brand = c3.text_input("Brand", d.get("brand", ""), key=f"{prefix}_brand")
        c1, c2, c3, c4 = st.columns(4)
        retail = c1.number_input("Retail price", min_value=0.0, value=float(d.get("retail_price", 1000.0)), key=f"{prefix}_rp")
        dprice = c2.number_input("Discount price", min_value=0.0, value=float(d.get("discount_price", 800.0)), key=f"{prefix}_dp")
        rating = c3.number_input("Rating (0-5)", 0.0, 5.0, float(d.get("rating", 4.0)), 0.1, key=f"{prefix}_rt")
        reviews = c4.number_input("Number of reviews", min_value=0, value=int(d.get("num_reviews", 0)), key=f"{prefix}_nr")
        c1, c2 = st.columns(2)
        seller = c1.text_input("Seller name", d.get("seller_name", ""), key=f"{prefix}_sel")
        cur = d.get("stock_status", "In stock")
        stock = c2.selectbox("Stock status", STOCK, index=STOCK.index(cur) if cur in STOCK else 0, key=f"{prefix}_ss")
        url = st.text_input("Product URL (optional)", d.get("product_url") or "", key=f"{prefix}_url")
        amt, pct, rcat, rng = derived(retail, dprice, rating)
        st.caption(f"Auto-calculated → discount ₹{amt} ({pct}%), rating category **{rcat}**, range **{rng}**")
        row = dict(product_id=int(pid), product_name=name, category=cat, sub_category=sub, brand=brand, retail_price=retail,
                   discount_price=dprice, discount_percentage=pct, discount_amount=amt, price_difference=round(dprice - retail, 2),
                   rating=rating, num_reviews=int(reviews), seller_name=seller, stock_status=stock, rating_category=rcat,
                   discount_range=rng, product_url=url or None)
        valid = bool(name.strip() and cat.strip() and seller.strip() and dprice <= retail)
        return row, valid

    t_create, t_read, t_update, t_delete = st.tabs(["➕ Create", "📖 Read", "✏️ Update", "🗑️ Delete"])

    with t_create:
        row, valid = product_form("new")
        if st.button("Add product", type="primary", disabled=not valid):
            try:
                write_product(row, new=True)
                st.success(f"Product {row['product_id']} added.")
            except Exception as e:  # noqa: BLE001
                st.error(f"Insert failed (duplicate ID?): {str(e)[:200]}")
        if not valid:
            st.caption("Name, category and seller are required, and the discount price cannot exceed the retail price.")

    with t_read:
        key = st.text_input("Search by product ID or name", key="read_q")
        lim = st.number_input("Rows", 5, 500, 25, key="read_n")
        if key.strip().isdigit():
            data = run_query(f"SELECT * FROM {MAIN} WHERE product_id = :k", {"k": int(key)})
        elif key.strip():
            data = run_query(f"SELECT * FROM {MAIN} WHERE product_name LIKE :k LIMIT {int(lim)}", {"k": f"%{key}%"})
        else:
            data = run_query(f"SELECT * FROM {MAIN} ORDER BY product_id DESC LIMIT {int(lim)}")
        show_df(data)

    with t_update:
        pid = st.number_input("Product ID to update", min_value=1, step=1, key="upd_pid")
        cur = run_query(f"""SELECT m.*, c.product_url FROM {MAIN} m LEFT JOIN category_catalog c USING (product_id)
                            WHERE m.product_id = :p""", {"p": int(pid)})
        if cur.empty:
            st.info("No product with that ID.")
        else:
            row, valid = product_form(f"upd{int(pid)}", cur.iloc[0].to_dict(), new=False)
            if st.button("Save changes", type="primary", disabled=not valid):
                try:
                    write_product(row, new=False)
                    st.success(f"Product {int(pid)} updated.")
                except Exception as e:  # noqa: BLE001
                    st.error(str(e)[:200])

    with t_delete:
        pid = st.number_input("Product ID to delete", min_value=1, step=1, key="del_pid")
        cur = run_query(f"SELECT product_id, product_name, brand, seller_name, retail_price FROM {MAIN} WHERE product_id = :p", {"p": int(pid)})
        if cur.empty:
            st.info("No product with that ID.")
        else:
            show_df(cur)
            sure = st.checkbox("I understand this permanently deletes the product from all tables")
            if st.button("Delete product", type="primary", disabled=not sure):
                with get_engine().begin() as con:
                    for t in ("seller_performance", "category_catalog", MAIN):
                        con.execute(text(f"DELETE FROM {t} WHERE product_id = :p"), {"p": int(pid)})
                st.cache_data.clear()
                st.success(f"Product {int(pid)} deleted.")

# ==========================================================================
# PAGE 5 - SQL QUERY EXPLORER
# ==========================================================================
elif page == "SQL Query Explorer":
    st.title("🧮 SQL Query Explorer")

    def load_queries():
        if not SQL_FILE.exists():
            return {}
        raw = SQL_FILE.read_text(encoding="utf-8")
        parts = re.split(r"(?m)^-- (Q\d+)\s+", raw)[1:]
        out = {}
        for i in range(0, len(parts), 2):
            title, _, body = parts[i + 1].partition("\n")
            out[f"{parts[i]} - {title.strip()}"] = body.split(";")[0].strip()
        return out

    queries = load_queries()
    tab1, tab2 = st.tabs(["Predefined business queries", "Custom SELECT query"])
    with tab1:
        if not queries:
            st.warning(f"{SQL_FILE} not found.")
        else:
            choice = st.selectbox("Choose a query", list(queries))
            st.code(queries[choice], language="sql")
            if st.button("▶ Run query", type="primary"):
                res = run_query(queries[choice])
                st.success(f"{len(res):,} rows returned")
                show_df(res)
                csv_button(res, "query_result.csv", key="q_csv")
    with tab2:
        sql = st.text_area("Write a SELECT statement", f"SELECT category, COUNT(*) AS products FROM {MAIN} GROUP BY category;", height=140)
        if st.button("▶ Run custom query"):
            stmt = sql.strip().rstrip(";")
            if not re.match(r"(?is)^\s*select\b", stmt) or re.search(r"(?i)\b(insert|update|delete|drop|alter|truncate|create|grant)\b", stmt) or ";" in stmt:
                st.error("Only a single read-only SELECT statement is allowed here.")
            else:
                try:
                    res = run_query(stmt)
                    st.success(f"{len(res):,} rows returned")
                    show_df(res)
                    csv_button(res, "custom_query_result.csv", key="cq_csv")
                except Exception as e:  # noqa: BLE001
                    st.error(str(e)[:300])
