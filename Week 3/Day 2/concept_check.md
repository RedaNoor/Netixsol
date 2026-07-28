# Concept Check: SQL Joins & Relational Database Analysis

### 1. Why do relational databases split data into multiple tables?
To eliminate redundancy and keep each fact stored in exactly one place. Instead of repeating a customer's details on every rental row, a `customer` table holds it once and `rental` references it via a foreign key. This avoids update anomalies (updating one field everywhere it's duplicated) and keeps data consistent.

### 2. Difference between INNER JOIN and LEFT JOIN
`INNER JOIN` returns only rows with a match in both tables, unmatched rows on either side are dropped entirely. 
`LEFT JOIN` keeps every row from the left table regardless of a match, filling in `NULL` for right-table columns when nothing matches. Use `LEFT JOIN` when you need to find "what's missing," e.g. customers who never rented anything.
**Example:**
```sql
-- INNER JOIN: only customers who have rented something
SELECT c.first_name FROM customer c JOIN rental r ON c.customer_id = r.customer_id;
 
-- LEFT JOIN: all customers, including those who never rented (rental columns = NULL)
SELECT c.first_name, r.rental_id FROM customer c LEFT JOIN rental r ON c.customer_id = r.customer_id;
```

### 3. When would you use a FULL OUTER JOIN?
When you need every row from both tables, matched where possible, with `NULL`s on whichever side has no match. e.g. comparing two customer lists from different systems to see who exists in one but not the other. It's mainly used for reconciliation or data-migration checks, not everyday business queries.
 
**Example:** Comparing two customer lists from different systems to spot who exists in only one:
```sql
SELECT a.email, b.email FROM system_a a FULL OUTER JOIN system_b b ON a.email = b.email
WHERE a.email IS NULL OR b.email IS NULL;
```
 


### 4. Why are Primary Keys and Foreign Keys important?
Primary Keys guarantee every row can be uniquely and reliably identified, with no duplicates or NULLs. Foreign Keys link tables together correctly and enforce that referenced data actually exists (e.g. a rental can't reference a customer that doesn't exist). Together they're what makes joins accurate instead of guesswork.

### 5. Explain normalization in simple words
Normalization means storing each piece of information in one place only, instead of repeating it everywhere it's needed. If a customer's email is stored once in a `customer` table, updating it means changing one row, not hunting down every duplicate copy across the database.

### 6. What is an ER Diagram?
A visual map of a database's tables, their columns, and how they connect through primary/foreign keys. It lets you see the whole schema's structure at a glance, which is far easier than reading through every `CREATE TABLE` statement to figure out how tables relate.

### 7. What happens if a JOIN condition is incorrect?
If the `ON` condition is wrong or missing, you can get a cross join (every row paired with every row), duplicated rows, or completely wrong matches. Often without an error, since the query still runs, it just returns misleading results. This makes incorrect join conditions especially dangerous, since they can go unnoticed if no one checks the row counts.