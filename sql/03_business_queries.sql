-- =====================================================================
-- Script 3: 20 business queries   (USE flipkart_db first)
-- Covers: COUNT/AVG/MAX/MIN, WHERE, GROUP BY, HAVING, ORDER BY,
--         subqueries, JOIN, UNION ALL, VIEW
-- =====================================================================
USE flipkart_db;

-- Q1  Total product listings and average customer rating
SELECT COUNT(*) AS total_listings, ROUND(AVG(rating),2) AS avg_rating FROM flipkart_other_products;

-- Q2  Min, max and average retail price
SELECT MIN(retail_price) AS min_price, MAX(retail_price) AS max_price, ROUND(AVG(retail_price),2) AS avg_price
FROM flipkart_other_products;

-- Q3  Min, max and average calculated discount percentage
SELECT ROUND(MIN(discount_percentage),2) AS min_disc, ROUND(MAX(discount_percentage),2) AS max_disc,
       ROUND(AVG(discount_percentage),2) AS avg_disc
FROM flipkart_other_products;

-- Q4  Products with discount percentage greater than 30%
SELECT product_id, product_name, retail_price, discount_price, discount_percentage
FROM flipkart_other_products WHERE discount_percentage > 30
ORDER BY discount_percentage DESC LIMIT 100;

-- Q5  Products rated 4.0 or higher
SELECT product_id, product_name, brand, rating, num_reviews
FROM flipkart_other_products WHERE rating >= 4.0 ORDER BY rating DESC, num_reviews DESC LIMIT 100;

-- Q6  Listings in each category and sub-category
SELECT category, sub_category, COUNT(*) AS listings
FROM flipkart_other_products GROUP BY category, sub_category ORDER BY category, listings DESC;

-- Q7  Average calculated discount percentage per category
SELECT category, ROUND(AVG(discount_percentage),2) AS avg_discount_pct
FROM flipkart_other_products GROUP BY category ORDER BY avg_discount_pct DESC;

-- Q8  Categories having more than 100 listings (HAVING)
SELECT category, COUNT(*) AS listings
FROM flipkart_other_products GROUP BY category HAVING COUNT(*) > 100 ORDER BY listings DESC;

-- Q9  Brands having more than 10 listings (HAVING)
SELECT brand, COUNT(*) AS listings
FROM flipkart_other_products GROUP BY brand HAVING COUNT(*) > 10 ORDER BY listings DESC;

-- Q10 Top 10 products with the highest discount percentage
SELECT product_id, product_name, brand, retail_price, discount_price, discount_percentage
FROM flipkart_other_products ORDER BY discount_percentage DESC, discount_amount DESC LIMIT 10;

-- Q11 Compare sellers by average rating and total reviews
SELECT seller_name, COUNT(*) AS listings, ROUND(AVG(rating),2) AS avg_rating, SUM(num_reviews) AS total_reviews
FROM seller_performance GROUP BY seller_name ORDER BY avg_rating DESC;

-- Q12 Sellers whose products have more than 10,000 reviews in total (HAVING)
SELECT seller_name, SUM(num_reviews) AS total_reviews
FROM seller_performance GROUP BY seller_name HAVING SUM(num_reviews) > 10000 ORDER BY total_reviews DESC;

-- Q13 Products whose discount price is higher than the average discount price (subquery)
SELECT product_id, product_name, discount_price
FROM flipkart_other_products
WHERE discount_price > (SELECT AVG(discount_price) FROM flipkart_other_products)
ORDER BY discount_price DESC LIMIT 100;

-- Q14 UNION ALL of both product tables (same column order, NULL for missing fields)
SELECT product_id, product_name, brand, retail_price, discount_price, discount_percentage,
       rating, num_reviews, seller_name, NULL AS product_url, 'flipkart_other_products' AS source_table
FROM flipkart_other_products
UNION ALL
SELECT product_id, product_name, brand, retail_price, discount_price, discount_percentage,
       rating, num_reviews, NULL AS seller_name, product_url, 'category_catalog' AS source_table
FROM category_catalog
LIMIT 200;

-- Q15 Join seller-summary view to product listings on seller_name
SELECT p.product_name, p.rating AS product_rating, p.num_reviews, p.stock_status,
       s.seller_avg_rating, s.seller_total_reviews
FROM flipkart_other_products p
JOIN seller_summary s ON p.seller_name = s.seller_name
ORDER BY s.seller_avg_rating DESC, p.rating DESC LIMIT 100;

-- Q16 Average retail vs discount price per category
SELECT category, ROUND(AVG(retail_price),2) AS avg_retail, ROUND(AVG(discount_price),2) AS avg_discount_price
FROM flipkart_other_products GROUP BY category ORDER BY avg_retail DESC;

-- Q17 Category-wise average rating
SELECT category, ROUND(AVG(rating),2) AS avg_rating FROM flipkart_other_products
GROUP BY category ORDER BY avg_rating DESC;

-- Q18 Stock status per seller
SELECT seller_name, stock_status, COUNT(*) AS listings
FROM seller_performance GROUP BY seller_name, stock_status ORDER BY seller_name, listings DESC;

-- Q19 Sellers with the highest average discount (JOIN main table)
SELECT p.seller_name, ROUND(AVG(p.discount_percentage),2) AS avg_discount_pct
FROM flipkart_other_products p GROUP BY p.seller_name ORDER BY avg_discount_pct DESC;

-- Q20 Products in the catalog with more reviews than the average (JOIN + subquery)
SELECT c.product_id, c.product_name, c.num_reviews, p.category
FROM category_catalog c JOIN flipkart_other_products p ON c.product_id = p.product_id
WHERE c.num_reviews > (SELECT AVG(num_reviews) FROM category_catalog)
ORDER BY c.num_reviews DESC LIMIT 50;
