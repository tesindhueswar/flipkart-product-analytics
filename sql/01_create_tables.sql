-- =====================================================================
-- Flipkart Product Analytics  |  Script 1: database + tables
-- Run:  mysql -u root -p < sql/01_create_tables.sql
-- =====================================================================
CREATE DATABASE IF NOT EXISTS flipkart_db;
USE flipkart_db;

DROP VIEW  IF EXISTS flipkart_products;
DROP VIEW  IF EXISTS seller_summary;
DROP TABLE IF EXISTS seller_performance;
DROP TABLE IF EXISTS category_catalog;
DROP TABLE IF EXISTS flipkart_other_products;

-- Table 1 : main product table
CREATE TABLE flipkart_other_products (
    product_id          INT PRIMARY KEY,
    product_name        VARCHAR(500),
    category            VARCHAR(100),
    sub_category        VARCHAR(100),
    brand               VARCHAR(150),
    retail_price        FLOAT,
    discount_price      FLOAT,
    discount_percentage FLOAT,
    discount_amount     FLOAT,
    price_difference    FLOAT,
    rating              FLOAT,
    review_count        INT,
    seller_name         VARCHAR(150),
    stock_status        VARCHAR(30),
    rating_category     VARCHAR(20),
    discount_range      VARCHAR(20)
);

-- Table 2 : category catalog
CREATE TABLE category_catalog (
    product_id          INT PRIMARY KEY,
    product_name        VARCHAR(500),
    brand               VARCHAR(150),
    retail_price        FLOAT,
    discount_price      FLOAT,
    discount_percentage FLOAT,
    discount_amount     FLOAT,
    rating              FLOAT,
    review_count        INT,
    product_url         TEXT
);

-- Table 3 : seller performance (one row per product-seller listing)
CREATE TABLE seller_performance (
    product_id      INT,
    product_name    VARCHAR(500),
    rating          FLOAT,
    review_count    INT,
    stock_status    VARCHAR(30),
    rating_category VARCHAR(20),
    seller_name     VARCHAR(150),
    PRIMARY KEY (product_id, seller_name)
);

-- Helpful indexes for analysis / dashboard filters
CREATE INDEX idx_fop_category ON flipkart_other_products (category, sub_category);
CREATE INDEX idx_fop_brand    ON flipkart_other_products (brand);
CREATE INDEX idx_fop_seller   ON flipkart_other_products (seller_name);
CREATE INDEX idx_sp_seller    ON seller_performance (seller_name);
