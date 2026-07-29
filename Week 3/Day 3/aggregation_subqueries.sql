
-- PART 1: AGGREGATION BASICS

-- 1. Total revenue generated per store
SELECT
    s.store_id,
    SUM(p.amount) AS total_revenue
FROM payment p
JOIN staff s ON p.staff_id = s.staff_id
GROUP BY s.store_id
ORDER BY s.store_id;


-- 2. Average rental duration per film category
SELECT
    c.name AS category,
    ROUND(AVG(f.rental_duration), 2) AS avg_rental_duration
FROM film f
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id
GROUP BY c.name
ORDER BY avg_rental_duration DESC;

-- 3. Number of rentals made each month
SELECT
    DATE_TRUNC('month', rental_date)::DATE AS rental_month,
    COUNT(*) AS num_rentals
FROM rental
GROUP BY DATE_TRUNC('month', rental_date)::DATE
ORDER BY rental_month;

-- 4. Categories with more than 50 films (HAVING filters the grouped result,
-- not the raw rows, since the film count only exists after grouping)
SELECT
    c.name AS category,
    COUNT(f.film_id) AS film_count
FROM film_category fc
JOIN category c ON fc.category_id = c.category_id
JOIN film f ON fc.film_id = f.film_id
GROUP BY c.name
HAVING COUNT(f.film_id) > 50
ORDER BY film_count DESC;


-- PART 2: SUBQUERY CHALLENGES

-- 5. Customers who spent more than the average customer spend
-- Inner query builds one total per customer, then averages those totals.
-- Outer query keeps only customers above that average.

SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    SUM(p.amount) AS total_spent
FROM customer c
JOIN payment p
    ON c.customer_id = p.customer_id
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name
HAVING SUM(p.amount) > (
    SELECT AVG(customer_total)
    FROM (
        SELECT SUM(amount) AS customer_total
        FROM payment
        GROUP BY customer_id
    ) AS customer_totals
)
ORDER BY total_spent DESC;

-- 6. Film(s) with the highest rental rate in each category (correlated subquery)
-- The inner query re-runs for every row of the outer query, filtered to
-- that row's own category_id (fc.category_id), which is what makes it correlated.
SELECT
    f.title,
    c.name AS category,
    f.rental_rate
FROM film f
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id
WHERE f.rental_rate = (
    SELECT MAX(f2.rental_rate)
    FROM film f2
    JOIN film_category fc2 ON f2.film_id = fc2.film_id
    WHERE fc2.category_id = fc.category_id
)
ORDER BY category, f.title;


-- 7. Customers who have never rented a film 
SELECT
    customer_id,
    first_name,
    last_name
FROM customer c
WHERE NOT EXISTS (
    SELECT 1
    FROM rental r
    WHERE r.customer_id = c.customer_id
);


-- 8. Store with the highest total revenue (subquery in WHERE)
SELECT
    store_id,
    total_revenue
FROM (
    SELECT
        s.store_id,
        SUM(p.amount) AS total_revenue
    FROM payment p
    JOIN staff s ON p.staff_id = s.staff_id
    GROUP BY s.store_id
) AS store_revenue
WHERE total_revenue = (
    SELECT MAX(total_revenue)
    FROM (
        SELECT
            s.store_id,
            SUM(p.amount) AS total_revenue
        FROM payment p
        JOIN staff s ON p.staff_id = s.staff_id
        GROUP BY s.store_id
    ) AS sub
);


-- PART 3: CTE & WINDOW FUNCTION CHALLENGES-- 

-- 9. Rank customers by total spend within each city (CTE)
WITH customer_spend AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        ci.city,
        SUM(p.amount) AS total_spent
    FROM customer c
    JOIN address a
        ON c.address_id = a.address_id
    JOIN city ci
        ON a.city_id = ci.city_id
    JOIN payment p
        ON c.customer_id = p.customer_id
    GROUP BY
        c.customer_id, c.first_name, c.last_name, ci.city
)
SELECT
    city,
    customer_id,
    customer_name,
    total_spent,
    RANK() OVER ( PARTITION BY city ORDER BY total_spent DESC) AS city_rank
FROM customer_spend
ORDER BY city, city_rank;


-- 10. Most recently rented film for each customer (ROW_NUMBER)
WITH ranked_rentals AS (
    SELECT r.customer_id,
           c.first_name || ' ' || c.last_name AS customer_name,
           f.title,
           r.rental_date,
           ROW_NUMBER() OVER (PARTITION BY r.customer_id ORDER BY r.rental_date DESC) AS rn
    FROM rental r
    JOIN customer c ON r.customer_id = c.customer_id
    JOIN inventory i ON r.inventory_id = i.inventory_id
    JOIN film f ON i.film_id = f.film_id
)
SELECT customer_id,
       customer_name,
       title AS most_recent_film,
       rental_date
FROM ranked_rentals
WHERE rn = 1
ORDER BY customer_id;


-- 11. Month-over-month rental revenue growth (CTE + LAG window function)
WITH monthly_revenue AS (
    SELECT DATE_TRUNC('month', payment_date)::DATE AS revenue_month,
           SUM(amount) AS revenue
    FROM payment
    GROUP BY DATE_TRUNC('month', payment_date)::DATE
)
SELECT revenue_month,
       revenue,
       LAG(revenue) OVER (ORDER BY revenue_month) AS prev_month_revenue,
       ROUND(
           (revenue - LAG(revenue) OVER (ORDER BY revenue_month))
           / NULLIF(LAG(revenue) OVER (ORDER BY revenue_month), 0) * 100,
           2
       ) AS growth_percent
FROM monthly_revenue
ORDER BY revenue_month;


-- 12. Top 3 highest-grossing films per category (RANK inside a CTE)
WITH film_revenue AS (
    SELECT
        f.film_id,
        f.title,
        c.name AS category,
        SUM(p.amount) AS revenue
    FROM film f
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    JOIN inventory i ON f.film_id = i.film_id
    JOIN rental r ON i.inventory_id = r.inventory_id
    JOIN payment p ON r.rental_id = p.rental_id
    GROUP BY f.film_id, f.title, c.name
),
ranked_films AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS category_rank
    FROM film_revenue
)
SELECT
    category,
    title,
    revenue,
    category_rank
FROM ranked_films
WHERE category_rank <= 3
ORDER BY category, category_rank;


-- BONUS CHALLENGE
-- Which staff member processed the highest revenue in each store,
-- and what percentage of that store's total revenue did they contribute?

WITH staff_revenue AS (
    SELECT s.staff_id,
           s.store_id,
           SUM(p.amount) AS staff_revenue
    FROM payment p
    JOIN staff s ON p.staff_id = s.staff_id
    GROUP BY s.staff_id, s.store_id
),
store_totals AS (
    SELECT store_id,
           SUM(staff_revenue) AS store_total
    FROM staff_revenue
    GROUP BY store_id
),
ranked_staff AS (
    SELECT sr.staff_id,
           sr.store_id,
           sr.staff_revenue,
           RANK() OVER (PARTITION BY sr.store_id ORDER BY sr.staff_revenue DESC) AS staff_rank
    FROM staff_revenue sr
)
SELECT rs.store_id,
       rs.staff_id,
       s.first_name || ' ' || s.last_name AS staff_name,
       rs.staff_revenue,
       st.store_total,
       ROUND(rs.staff_revenue / st.store_total * 100, 2) AS pct_of_store_revenue
FROM ranked_staff rs
JOIN store_totals st ON rs.store_id = st.store_id
JOIN staff s ON rs.staff_id = s.staff_id
WHERE rs.staff_rank = 1
ORDER BY rs.store_id;