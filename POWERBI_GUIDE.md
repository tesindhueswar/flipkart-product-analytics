# Power BI Dashboard — step-by-step (≈ 40 minutes)

## 1. Connect to the data
**Easiest:** Home → Get data → Text/CSV → `data/other_products_cleaned.csv` → Load.  
**MySQL:** Get data → MySQL database → server `localhost`, database `flipkart_db` → pick `flipkart_other_products`,
`category_catalog`, `seller_performance` (needs the MySQL Connector/NET driver from mysql.com).
Rename the table to **Products**. Check data types: prices/percentages = Decimal, `num_reviews` = Whole number.

## 2. Create measures (Modeling → New measure)
```DAX
Total Products      = COUNTROWS(Products)
Avg Rating          = AVERAGE(Products[rating])
Avg Discount %      = AVERAGE(Products[discount_percentage]) / 100
Avg Retail Price    = AVERAGE(Products[retail_price])
Avg Discount Price  = AVERAGE(Products[discount_price])
Total Reviews       = SUM(Products[num_reviews])
Total Discount Amt  = SUM(Products[discount_amount])
Out of Stock %      = DIVIDE(CALCULATE([Total Products], Products[stock_status] = "Out of stock"), [Total Products])
High Discount Items = CALCULATE([Total Products], Products[discount_percentage] > 30)
```
Format `Avg Discount %` and `Out of Stock %` as percentage.

## 3. Build 3 pages

### Page 1 — Overview (Q1-Q9)
| visual | fields | answers |
|---|---|---|
| 4 KPI **Cards** | Total Products, Avg Rating, Avg Discount %, Avg Retail Price | KPIs |
| **Bar** | Axis `category`, Values Total Products | Q1, Q2 |
| **Bar** (top 10 filter) | Axis `brand`, Values Total Products | Q3 |
| **Treemap** | Group `category`, Details `sub_category`, Values Total Products | Q1, Q4 |
| **Clustered column** | Axis `category`, Values Avg Retail Price + Avg Discount Price | Q5, Q8 |
| **Bar** | Axis `category`, Values Avg Discount % | Q6 |
| **Table** (Top N = 10 by `discount_amount`) | product_name, brand, retail_price, discount_price, discount_amount | Q7 |
| **Column** | Axis `discount_range`, Values Total Products | Q9 |

### Page 2 — Ratings & Reviews (Q10-Q13)
| visual | fields | answers |
|---|---|---|
| **Donut** | Legend `rating_category`, Values Total Products | Q10 |
| **Column** (bin `rating` size 0.5) | Axis rating bins, Values Total Products | Q10 |
| **Bar** | Axis `category`, Values Avg Rating (sort desc) | Q11 |
| **Table** (Top N = 10 by num_reviews) | product_name, brand, rating, num_reviews | Q12 |
| **Scatter** | X `rating`, Y `num_reviews`, Details `product_id` (or `category`) | Q13 |

### Page 3 — Seller Performance (Q14-Q17)
| visual | fields | answers |
|---|---|---|
| **Bar** | Axis `seller_name`, Values Total Products | Q14 |
| **Bar** | Axis `seller_name`, Values Avg Rating | Q15 |
| **Bar** | Axis `seller_name`, Values Avg Discount % | Q16 |
| **Stacked column** | Axis `seller_name`, Legend `stock_status`, Values Total Products | Q17 |
| **Donut** | Legend `stock_status`, Values Total Products | stock split |
| **Table** | seller_name, Total Products, Avg Rating, Total Reviews | seller table |

## 4. Slicers (copy to every page via View → Sync slicers)
`category`, `sub_category`, `brand`, `seller_name`, `stock_status`, `rating` (between), `retail_price` (between).

## 5. Polish & save
* Page titles, consistent theme (View → Themes), tooltips on.
* Add a short text box with the key insight under each chart.
* File → Save as `Flipkart_Dashboard.pbix`; export PDF (File → Export) and add screenshots to the GitHub repo.
