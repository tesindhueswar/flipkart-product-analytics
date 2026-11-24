-- =====================================================================
-- Script 2: standardise column names across tables
--   review_count -> num_reviews   (all tables)
--   (seller -> seller_name is already applied while cleaning in the notebook)
-- Run ONCE right after 01_create_tables.sql and BEFORE loading the data.
-- =====================================================================
USE flipkart_db;

ALTER TABLE flipkart_other_products CHANGE review_count num_reviews INT;
ALTER TABLE category_catalog        CHANGE review_count num_reviews INT;
ALTER TABLE seller_performance      CHANGE review_count num_reviews INT;

-- Phase-3 name "flipkart_products" is exposed as a view of the main table
CREATE OR REPLACE VIEW flipkart_products AS SELECT * FROM flipkart_other_products;

-- Seller summary view (used by Query 15 and the Streamlit app)
CREATE OR REPLACE VIEW seller_summary AS
SELECT  seller_name,
        COUNT(*)                    AS total_listings,
        ROUND(AVG(rating), 2)       AS seller_avg_rating,
        SUM(num_reviews)            AS seller_total_reviews
FROM    seller_performance
GROUP BY seller_name;
