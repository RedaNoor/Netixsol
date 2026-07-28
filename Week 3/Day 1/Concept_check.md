# Concept Check: SQL Foundations for Data Science

---

### 1. What problem does SQL solve that CSV files cannot?
CSVs are flat text files with no enforced structure, no relationships, and no protection against bad data. SQL databases scale to millions/billions of rows without loading everything into memory, enforce data integrity through constraints, link related tables together, and allow multiple users to read/write safely at once.

**Example:** Finding total sales by region across 10 million rows:
```sql
SELECT region, SUM(sales) FROM superstore_sales GROUP BY region;
```
This runs efficiently inside the database. Doing the same on a 10-million-row CSV in Excel would likely be unworkably slow, or simply impossible to even open.

### 2. What is the difference between a database table and a spreadsheet?
They look similar on the surface (both are rows and columns), but they behave very differently:

| Aspect | Spreadsheet (Excel) | Database Table |
|---|---|---|
| Data types | Loosely enforced,  a "number" column can still accept text | Strictly enforced, a column defined as `INTEGER` will reject text |
| Size | Practical limit around a few hundred thousand rows before it slows down | Handles millions/billions of rows efficiently |
| Relationships | No built-in way to link one sheet to another | Tables link via foreign keys, avoiding duplicated data |
| Validation | Manual (conditional formatting, data validation add-ons) | Built-in constraints (`NOT NULL`, `CHECK`, `UNIQUE`, `PRIMARY KEY`) |


**Example:** In a spreadsheet, nothing stops you from typing "twenty" into a column meant to hold a price. In a database table defined as `price NUMERIC(10,2)`, that same input would be rejected outright.

### 3. What is a Primary Key?
A column (or set of columns) that uniquely identifies every row in a table; no duplicates, no NULLs allowed. 
Example: `row_id INTEGER PRIMARY KEY` in `superstore_sales` guarantees every row has a distinct ID.

### 4. What is a Foreign Key?
A column in one table that references the Primary Key of another table, linking the two. 
Example: `orders.customer_id` referencing `customers.customer_id` ties each order to a real customer without duplicating customer info in every order row.

### 5. What is the difference between WHERE and HAVING?
`WHERE` filters individual rows *before* grouping/aggregation and can't use aggregate functions like `SUM()`. 
`HAVING` filters *after* `GROUP BY`, specifically on aggregated values, e.g. `HAVING SUM(sales) > 50000`.

### 6. What is the difference between ORDER BY and GROUP BY?
`ORDER BY` just sorts the final results without changing row count. 
`GROUP BY` collapses multiple rows into one row per group, usually paired with an aggregate like `SUM()` or `COUNT()`.

### 7. What does DISTINCT do?
Removes duplicates from the result, returning only unique values or unique combinations of the selected columns. 
Example: `SELECT DISTINCT region FROM superstore_sales;` lists each region once.

### 8. When should you use LIMIT?
Use it to preview data, get "top N" results (with `ORDER BY`), or avoid pulling excessive rows when testing a query. Example: `SELECT * FROM superstore_sales LIMIT 10;`.

### 9. What are aggregate functions?
Functions that collapse multiple rows into one summary value,  `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`. Most useful combined with `GROUP BY`, e.g. average profit per category.

### 10. Why do Data Scientists prefer databases over Excel for large datasets?
Databases scale far beyond Excel's ~1M row limit, query faster through indexing, enforce data integrity, support concurrent access, and integrate directly into code/pipelines (e.g. `pd.read_sql()`).  Excel workflows are slower, manual, and harder to reproduce.