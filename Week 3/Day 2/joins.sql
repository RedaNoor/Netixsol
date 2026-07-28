-- PART 1: RELATIONSHIP DISCOVERY
-- Identify the primary key of each table
SELECT tc.table_name, kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- Identify the foreign keys (and what they reference)
SELECT
    tc.table_name AS child_table,
    kcu.column_name AS fk_column,
    ccu.table_name AS parent_table,
    ccu.column_name AS parent_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- PART 2: SQL JOIN CHALLENGES

-- 1. Display Customer Name, Email, City, and Country
SELECT
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    ci.city,
    co.country
FROM customer c
JOIN address a ON c.address_id = a.address_id
JOIN city ci ON a.city_id = ci.city_id
JOIN country co ON ci.country_id = co.country_id;

-- 2. Display every payment with Customer Name, Film Title, and Amount Paid
SELECT
    c.first_name || ' ' || c.last_name AS customer_name,
    f.title AS film_title,
    p.amount AS amount_paid
FROM payment p
JOIN customer c ON p.customer_id = c.customer_id
JOIN rental r ON p.rental_id = r.rental_id
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN film f ON i.film_id = f.film_id;

-- 3. Display every payment with Customer Name, Film Title, and Amount Paid
-- (Same query as Question 2 in the task sheet applies)

-- 4. Find the Top 10 customers based on total amount spent
SELECT
    c.first_name || ' ' || c.last_name AS customer_name,
    SUM(p.amount) AS total_spent
FROM customer c
JOIN payment p ON c.customer_id = p.customer_id
GROUP BY c.customer_id, customer_name
ORDER BY total_spent DESC
LIMIT 10;

-- 5. Display each film with its Category and Rental Rate
SELECT
    f.title,
    cat.name AS category,
    f.rental_rate
FROM film f
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category cat ON fc.category_id = cat.category_id;

-- 6. Find all actors who appeared in each film
SELECT
    f.title,
    STRING_AGG(a.first_name || ' ' || a.last_name, ', ') AS actors
FROM film f
JOIN film_actor fa ON f.film_id = fa.film_id
JOIN actor a ON fa.actor_id = a.actor_id
GROUP BY f.film_id, f.title
ORDER BY f.title;

-- 7. Count how many films belong to each category
SELECT
    cat.name AS category,
    COUNT(fc.film_id) AS total_films
FROM category AS cat
LEFT JOIN film_category AS fc
    ON cat.category_id = fc.category_id
GROUP BY cat.category_id, cat.name
ORDER BY total_films DESC;

-- 8. Which categories generated the highest revenue?
SELECT
    cat.name AS category,
    SUM(p.amount) AS total_revenue
FROM category cat
JOIN film_category fc ON cat.category_id = fc.category_id
JOIN film f ON fc.film_id = f.film_id
JOIN inventory i ON f.film_id = i.film_id
JOIN rental r ON i.inventory_id = r.inventory_id
JOIN payment p ON r.rental_id = p.rental_id
GROUP BY cat.name
ORDER BY total_revenue DESC;

-- 9. Find customers who have rented more than 20 films
SELECT
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(r.rental_id) AS total_rentals
FROM customer c
JOIN rental r ON c.customer_id = r.customer_id
GROUP BY c.customer_id, customer_name
HAVING COUNT(r.rental_id) > 20
ORDER BY total_rentals DESC;

-- 10. Which cities generated the highest rental revenue?
SELECT
    ci.city,
    SUM(p.amount) AS total_revenue
FROM city ci
JOIN address a ON ci.city_id = a.city_id
JOIN customer c ON a.address_id = c.address_id
JOIN payment p ON c.customer_id = p.customer_id
GROUP BY ci.city
ORDER BY total_revenue DESC;

-- BONUS Challenge
-- Determine the shortest path of table joins needed to answer:
-- **Which actor has generated the highest total rental revenue?**'
SELECT
    a.actor_id,
    CONCAT(a.first_name, ' ', a.last_name) AS actor_name,
    SUM(p.amount) AS total_revenue
FROM actor a
JOIN film_actor fa ON a.actor_id = fa.actor_id
JOIN film f ON fa.film_id = f.film_id
JOIN inventory i ON f.film_id = i.film_id
JOIN rental r ON i.inventory_id = r.inventory_id
JOIN payment p ON r.rental_id = p.rental_id
GROUP BY a.actor_id, actor_name
ORDER BY total_revenue DESC
LIMIT 1;