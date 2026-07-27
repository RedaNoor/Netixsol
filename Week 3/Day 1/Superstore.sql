 -- Create table with constraints
CREATE TABLE superstore_sales (
    row_id INTEGER PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    order_date DATE NOT NULL,
    ship_date DATE,
    ship_mode VARCHAR(50),
    customer_id VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    segment VARCHAR(50),
    country VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(10),
    region VARCHAR(50),
    product_id VARCHAR(20) NOT NULL,
    category VARCHAR(50),
    sub_category VARCHAR(50),
    product_name VARCHAR(200) NOT NULL,
    sales DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    discount DECIMAL(4,2) CHECK (discount >= 0 AND discount <= 1),
    profit DECIMAL(10,2)
);

-- Count total rows
SELECT COUNT(*) FROM superstore_sales;

-- Preview first 10 rows
SELECT * FROM superstore_sales LIMIT 10;

-- Inspect table structure
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'superstore_sales'
ORDER BY ordinal_position;

-- Information schema query
SELECT *
FROM information_schema.columns
WHERE table_name = 'superstore_sales';