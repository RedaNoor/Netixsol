# SQL Foundations for Data Science

## Overview

This project covers the fundamentals of relational databases using PostgreSQL, applied to the Superstore Sales dataset. It includes database setup, table creation with constraints, CSV import, and foundational SQL queries (filtering, sorting, aggregation, and metadata inspection).

## Dataset

**Source:** [Superstore Dataset (Kaggle)](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)

The dataset (`superstore_dataset.csv`) contains 9,994 retail order records across 21 columns, including order details, customer information, product categories, and sales/profit figures.

## Setup Steps

### 1. Install Prerequisites
- Install [PostgreSQL](https://www.postgresql.org/download/) (includes the PostgreSQL Server and command-line tools).
- Install [pgAdmin 4](https://www.pgadmin.org/download/) for database management via GUI.
- Stack Builder is not required for this project.

### 2. Create the Database (via pgAdmin UI)
1. In the pgAdmin sidebar, right-click **Databases** → **Create** → **Database...**
2. Set the **Database** name to `super_store_db`.
3. Leave the remaining fields default and click **Save**.

### 3. Create the Table
1. Expand `super_store_db → Schemas → public`.
2. Right-click **Tables** → **Create** → **Table...**
3. Right click on Table → Query tool
(Paste the code given below and run)
```sql
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
```

### 4. Import the CSV (via pgAdmin UI)
1. Right-click the new `superstore_sales` table → **Import/Export Data...**
2. Toggle the switch to **Import**.
3. Under **Filename**, browse to and select `superstore_dataset.csv`.
4. Set **Format** to `csv`.
5. On the **Options** tab: turn **Header** ON, set **Delimiter** to `,`, and **Quote character** to `"`.
6. Click **Import** and confirm the success message once complete.

### 6. Verify the Import
```sql
SELECT COUNT(*) FROM superstore_sales;

SELECT * FROM superstore_sales LIMIT 10;

SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'superstore_sales'
ORDER BY ordinal_position;
```

## Repository Contents
- `README.md` — this file
- `sql/setup.sql` — database, table creation, and import commands
- `sql/queries.sql` — SELECT, WHERE, ORDER BY, GROUP BY, and aggregate query examples
- `concept_check.md` — answers to the concept check questions
- `screenshots/` — database creation, table import, table structure, query results, and `information_schema.columns` output
- `superstore_dataset.csv` — the source dataset (or a note on its download source, if excluded for size)

## Tools Used
- PostgreSQL 18
- pgAdmin 4