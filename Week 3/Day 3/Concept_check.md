# Concept Check

### 1. What is the difference between WHERE and HAVING?

WHERE filters the raw rows before anything gets grouped. HAVING filters after GROUP BY has already done its thing, so it works on the grouped totals instead of individual rows.

Basically if I want to filter on something like SUM() or COUNT(), it has to be HAVING, since that number doesn't exist yet when WHERE runs.

```sql
-- WHERE, filtering raw rows
SELECT * FROM payment WHERE amount > 5;

-- HAVING, filtering after grouping
SELECT customer_id, SUM(amount) AS total_spent
FROM payment
GROUP BY customer_id
HAVING SUM(amount) > 150;
```

---

### 2. When would you use a correlated subquery instead of a JOIN?

When the inner query actually needs info from the outer row to run, like "give me the max rate in THIS film's category." A regular join can't really do a per-row comparison like that on its own, it just combines tables. A correlated subquery re-runs once per outer row because it's referencing that row.

```sql
SELECT f.title, c.name
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

### 3. What is a CTE, and why is it more readable than a nested subquery?

A CTE is just a query you name using WITH, so you can reuse it or build on it later in the same statement. It's basically a temporary named result that only exists while that query runs.

The reason it's more readable is nested subqueries force you to read from the inside out, which gets confusing fast once you're 2-3 levels deep. A CTE reads top to bottom like steps: do this first, then do that with it.

```sql
WITH customer_totals AS (
    SELECT customer_id, SUM(amount) AS total_spent
    FROM payment
    GROUP BY customer_id
)
SELECT * FROM customer_totals WHERE total_spent > 100;
```

---

### 4. Explain the difference between RANK() and DENSE_RANK().

Both give a ranking, the only difference is what happens after a tie.

RANK() leaves a gap, so if two rows tie for 2nd, the next row jumps to 4th. DENSE_RANK() doesn't leave that gap, so the next row is just 3rd.

| score | RANK() | DENSE_RANK() |
|---|---|---|
| 98 | 1 | 1 |
| 92 | 2 | 2 |
| 92 | 2 | 2 |
| 88 | 4 | 3 |

---

### 5. What does PARTITION BY do differently from GROUP BY?

GROUP BY squashes everything into one row per group, you lose the individual rows. PARTITION BY keeps every row but still lets you calculate something per group, like a running total or a rank, right next to the original data.

```sql
SELECT customer_id, amount,
       SUM(amount) OVER (PARTITION BY customer_id) AS total_spent
FROM payment;
```

Here you still see every payment row, just with each customer's total tagged on next to it.

---

### 6. Can a subquery return multiple rows? What operator would you use in that case?

Yeah, plenty of subqueries return more than one row, you just can't use = on those, since = only expects one value. Instead use IN, NOT IN, EXISTS, NOT EXISTS, ANY, or ALL.

```sql
SELECT * FROM customer
WHERE customer_id IN (
    SELECT customer_id FROM payment WHERE amount > 10
);
```

---

### 7. Give an example of when CASE WHEN is useful inside an aggregate function.

When we want to count or sum only rows that meet some condition, without writing a separate query for it. It's basically a way to sneak an if/else into an aggregate.

```sql
SELECT
    SUM(CASE WHEN amount > 5 THEN amount ELSE 0 END) AS high_value_revenue,
    SUM(CASE WHEN amount > 5 THEN 1 ELSE 0 END) AS high_value_payments
FROM payment;
```

Both numbers come out of the same table scan instead of running two separate queries.