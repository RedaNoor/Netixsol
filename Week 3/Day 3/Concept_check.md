# Concept Check: SQL Aggregation, Subqueries & CTEs

## 1. What is the difference between `WHERE` and `HAVING`?

- `WHERE` filters rows **before** grouping.
- `HAVING` filters groups **after** `GROUP BY`.
- `WHERE` cannot use aggregate functions, while `HAVING` can.

**Example:**

```sql
-- WHERE filters rows
SELECT *
FROM payment
WHERE amount > 5;
```

```sql
-- HAVING filters groups
SELECT customer_id, SUM(amount) AS total_spent
FROM payment
GROUP BY customer_id
HAVING SUM(amount) > 150;
```

---

## 2. When would you use a correlated subquery instead of a JOIN?

A correlated subquery is used when the inner query depends on the current row of the outer query. It executes once for each row returned by the outer query.

**Example:**

```sql
SELECT c.name, f.title
FROM film f
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id
WHERE f.rental_rate = (
    SELECT MAX(f2.rental_rate)
    FROM film f2
    JOIN film_category fc2 ON f2.film_id = fc2.film_id
    WHERE fc2.category_id = fc.category_id
);
```

---

## 3. What is a CTE, and why is it more readable than a nested subquery?

A **Common Table Expression (CTE)** is a temporary result set created using the `WITH` clause. It exists only during the execution of the query.

CTEs improve readability because they:
- Break complex queries into smaller steps.
- Give meaningful names to intermediate results.
- Make queries easier to read, debug, and maintain.

**Example:**

```sql
WITH customer_totals AS (
    SELECT customer_id, SUM(amount) AS total_spent
    FROM payment
    GROUP BY customer_id
)
SELECT *
FROM customer_totals
WHERE total_spent > 100;
```

---

## 4. Explain the difference between `RANK()` and `DENSE_RANK()`.

Both functions assign rankings, but they handle ties differently.

- `RANK()` skips the next rank after a tie.
- `DENSE_RANK()` does not skip ranks.

| Score | RANK() | DENSE_RANK() |
|------:|-------:|-------------:|
| 98 | 1 | 1 |
| 92 | 2 | 2 |
| 92 | 2 | 2 |
| 88 | 4 | 3 |

---

## 5. What does `PARTITION BY` do differently from `GROUP BY`?

- `GROUP BY` combines rows into one row per group.
- `PARTITION BY` keeps all rows and performs calculations separately within each partition.

**Example:**

```sql
SELECT customer_id,
       amount,
       SUM(amount) OVER (PARTITION BY customer_id) AS total_spent
FROM payment;
```

---

## 6. Can a subquery return multiple rows? What operator would you use in that case?

Yes. A subquery can return multiple rows.

Use operators such as:

- `IN`
- `NOT IN`
- `EXISTS`
- `NOT EXISTS`
- `ANY`
- `ALL`

**Example:**

```sql
SELECT *
FROM customer
WHERE customer_id IN (
    SELECT customer_id
    FROM payment
    WHERE amount > 10
);
```

---

## 7. Give an example of when `CASE WHEN` is useful inside an aggregate function.

`CASE WHEN` is commonly used for **conditional aggregation**, where only rows meeting a condition are included in the calculation.

**Example: Sum payments greater than $5**

```sql
SELECT
    SUM(CASE
            WHEN amount > 5 THEN amount
            ELSE 0
        END) AS high_value_revenue
FROM payment;
```

**Example: Count payments greater than $5**

```sql
SELECT
    SUM(CASE
            WHEN amount > 5 THEN 1
            ELSE 0
        END) AS high_value_payments
FROM payment;
```