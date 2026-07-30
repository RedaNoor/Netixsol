-- Music Store Business Intelligence Pipeline
WITH customer_invoice_summary AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS full_name,
        c.country,
        COUNT(DISTINCT i.invoice_id)                        AS total_invoices,
        SUM(i.total)                                        AS total_spent,
        ROUND(AVG(i.total), 2)                              AS avg_invoice_value,
        COUNT(DISTINCT DATE_TRUNC('month', i.invoice_date)) AS purchase_months
    FROM customer c
    JOIN invoice i ON i.customer_id = c.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.country
),

customer_catalog_summary AS (
    SELECT
        c.customer_id,
        SUM(il.quantity)             AS total_tracks_purchased,
        COUNT(DISTINCT t.genre_id)   AS unique_genres,
        COUNT(DISTINCT al.artist_id) AS unique_artists
    FROM customer c
    JOIN invoice i       ON i.customer_id = c.customer_id
    JOIN invoice_line il ON il.invoice_id = i.invoice_id
    JOIN track t         ON t.track_id = il.track_id
    LEFT JOIN album al   ON al.album_id = t.album_id
    GROUP BY c.customer_id
),

-- Task 1: reusable customer profile
customer_profile AS (
    SELECT
        cis.customer_id, cis.full_name, cis.country,
        cis.total_spent, cis.total_invoices, cis.avg_invoice_value, cis.purchase_months,
        COALESCE(ccs.total_tracks_purchased, 0) AS total_tracks_purchased,
        COALESCE(ccs.unique_genres, 0)          AS unique_genres,
        COALESCE(ccs.unique_artists, 0)         AS unique_artists
    FROM customer_invoice_summary cis
    LEFT JOIN customer_catalog_summary ccs ON ccs.customer_id = cis.customer_id
),

-- Task 2: segmentation
customer_quartiles AS (
    SELECT
        cp.*,
        NTILE(4) OVER (ORDER BY cp.total_spent DESC, cp.customer_id)      AS spend_quartile,
        NTILE(4) OVER (ORDER BY cp.purchase_months DESC, cp.customer_id)   AS frequency_quartile,
        NTILE(4) OVER (ORDER BY cp.unique_genres DESC, cp.customer_id)     AS genre_quartile,
        NTILE(4) OVER (ORDER BY cp.unique_artists DESC, cp.customer_id)    AS artist_quartile
    FROM customer_profile cp
),
customer_scorecard AS (
    SELECT
        cq.customer_id, cq.full_name, cq.country, cq.total_spent,
        cq.total_invoices, cq.purchase_months, cq.unique_genres, cq.unique_artists,
        (
            (5 - cq.spend_quartile) * 2 +
            (5 - cq.frequency_quartile) +
            (5 - cq.genre_quartile) +
            (5 - cq.artist_quartile)
        ) AS loyalty_points
    FROM customer_quartiles cq
),
customer_loyalty_quartile AS (
    SELECT
        cs.*,
        NTILE(4) OVER (ORDER BY cs.loyalty_points DESC, cs.customer_id) AS loyalty_quartile
    FROM customer_scorecard cs
),
customer_segments AS (
    SELECT
        clq.customer_id,
        clq.full_name,
        clq.country,
        clq.total_spent,
        clq.loyalty_points,
        CASE clq.loyalty_quartile
            WHEN 1 THEN 'Platinum'
            WHEN 2 THEN 'Gold'
            WHEN 3 THEN 'Silver'
            ELSE 'Bronze'
        END AS customer_segment
    FROM customer_loyalty_quartile clq
),

-- Task 3: favorite genre + campaign
customer_genre_purchases AS (
    SELECT
        c.customer_id,
        g.name           AS genre_name,
        SUM(il.quantity) AS tracks_bought,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_id
            ORDER BY SUM(il.quantity) DESC, g.name ASC
        ) AS genre_preference_rank
    FROM customer c
    JOIN invoice i       ON i.customer_id = c.customer_id
    JOIN invoice_line il ON il.invoice_id = i.invoice_id
    JOIN track t         ON t.track_id = il.track_id
    JOIN genre g         ON g.genre_id = t.genre_id
    GROUP BY c.customer_id, g.name
),
customer_favorite_genre AS (
    SELECT customer_id, genre_name AS favorite_genre, tracks_bought
    FROM customer_genre_purchases
    WHERE genre_preference_rank = 1
),
customer_marketing_plan AS (
    SELECT
        cs.customer_id, cs.full_name, cs.country,
        cs.customer_segment, cs.total_spent, cfg.favorite_genre,
        CASE cs.customer_segment
            WHEN 'Platinum' THEN 'Early access to new releases'
            WHEN 'Gold'     THEN 'Curated album bundle offer'
            WHEN 'Silver'   THEN 'Discount on their favorite genre'
            ELSE 'Welcome coupon on first purchase'
        END AS campaign
    FROM customer_segments cs
    LEFT JOIN customer_favorite_genre cfg ON cfg.customer_id = cs.customer_id
),

-- Task 4: country expansion score
country_revenue_metrics AS (
    SELECT
        cp.country,
        COUNT(DISTINCT cp.customer_id)                                            AS total_customers,
        SUM(cp.total_spent)                                                       AS total_revenue,
        ROUND(SUM(cp.total_spent) / NULLIF(COUNT(DISTINCT cp.customer_id), 0), 2) AS avg_revenue_per_customer,
        ROUND(SUM(cp.total_spent) / NULLIF(SUM(cp.total_invoices), 0), 2)         AS avg_invoice_value
    FROM customer_profile cp
    GROUP BY cp.country
),
country_catalog_breadth AS (
    SELECT
        c.country,
        COUNT(DISTINCT t.genre_id) AS genres_purchased
    FROM customer c
    JOIN invoice i       ON i.customer_id = c.customer_id
    JOIN invoice_line il ON il.invoice_id = i.invoice_id
    JOIN track t         ON t.track_id = il.track_id
    GROUP BY c.country
),
country_customer_diversity AS (
    SELECT
        country,
        COUNT(DISTINCT customer_segment) AS customer_diversity
    FROM customer_segments
    GROUP BY country
),
country_profile AS (
    SELECT
        rm.country, rm.total_customers, rm.total_revenue,
        rm.avg_revenue_per_customer, rm.avg_invoice_value,
        COALESCE(cb.genres_purchased, 0)    AS genres_purchased,
        COALESCE(cd.customer_diversity, 0)  AS customer_diversity
    FROM country_revenue_metrics rm
    LEFT JOIN country_catalog_breadth cb    ON cb.country = rm.country
    LEFT JOIN country_customer_diversity cd ON cd.country = rm.country
),
country_normalized AS (
    SELECT
        cp.*,
        cp.avg_revenue_per_customer::numeric / NULLIF(MAX(cp.avg_revenue_per_customer) OVER (), 0) AS n_rev_per_customer,
        cp.total_revenue::numeric            / NULLIF(MAX(cp.total_revenue) OVER (), 0)            AS n_total_revenue,
        cp.total_customers::numeric          / NULLIF(MAX(cp.total_customers) OVER (), 0)          AS n_total_customers,
        cp.avg_invoice_value::numeric        / NULLIF(MAX(cp.avg_invoice_value) OVER (), 0)        AS n_avg_invoice,
        cp.genres_purchased::numeric         / NULLIF(MAX(cp.genres_purchased) OVER (), 0)         AS n_genre_breadth,
        cp.customer_diversity::numeric       / NULLIF(MAX(cp.customer_diversity) OVER (), 0)       AS n_customer_diversity
    FROM country_profile cp
),
country_expansion_score AS (
    SELECT
        cn.country, cn.total_customers, cn.total_revenue,
        cn.avg_revenue_per_customer, cn.avg_invoice_value,
        cn.genres_purchased, cn.customer_diversity,
        ROUND(
            (cn.n_rev_per_customer   * 0.30 +
             cn.n_total_revenue      * 0.25 +
             cn.n_total_customers    * 0.15 +
             cn.n_avg_invoice        * 0.10 +
             cn.n_genre_breadth      * 0.10 +
             cn.n_customer_diversity * 0.10) * 100
        , 2) AS expansion_score,
        RANK() OVER (
            ORDER BY
                (cn.n_rev_per_customer   * 0.30 +
                 cn.n_total_revenue      * 0.25 +
                 cn.n_total_customers    * 0.15 +
                 cn.n_avg_invoice        * 0.10 +
                 cn.n_genre_breadth      * 0.10 +
                 cn.n_customer_diversity * 0.10) DESC
        ) AS country_rank
    FROM country_normalized cn
),

-- Task 5 helper CTEs
segment_genre_tally AS (
    SELECT
        cs.customer_segment,
        cfg.favorite_genre,
        COUNT(*) AS fans_in_segment,
        RANK() OVER (
            PARTITION BY cs.customer_segment
            ORDER BY COUNT(*) DESC
        ) AS genre_rank_in_segment
    FROM customer_segments cs
    JOIN customer_favorite_genre cfg ON cfg.customer_id = cs.customer_id
    GROUP BY cs.customer_segment, cfg.favorite_genre
),
segment_top_genre AS (
    SELECT customer_segment, favorite_genre AS top_genre, fans_in_segment
    FROM segment_genre_tally
    WHERE genre_rank_in_segment = 1
),
artist_leaderboard AS (
    SELECT
        ar.artist_id,
        ar.name AS artist_name,
        SUM(il.unit_price * il.quantity) AS total_revenue,
        RANK() OVER (ORDER BY SUM(il.unit_price * il.quantity) DESC) AS artist_rank
    FROM artist ar
    JOIN album al        ON al.artist_id = ar.artist_id
    JOIN track t         ON t.album_id = al.album_id
    JOIN invoice_line il ON il.track_id = t.track_id
    GROUP BY ar.artist_id, ar.name
),
album_leaderboard AS (
    SELECT
        al.album_id,
        al.title AS album_title,
        ar.name  AS artist_name,
        SUM(il.unit_price * il.quantity) AS total_revenue,
        RANK() OVER (ORDER BY SUM(il.unit_price * il.quantity) DESC) AS album_rank
    FROM album al
    JOIN artist ar        ON ar.artist_id = al.artist_id
    JOIN track t          ON t.album_id = al.album_id
    JOIN invoice_line il  ON il.track_id = t.track_id
    GROUP BY al.album_id, al.title, ar.name
),
employee_leaderboard AS (
    SELECT
        e.employee_id,
        e.first_name || ' ' || e.last_name AS employee_name,
        e.title,
        COUNT(DISTINCT c.customer_id)            AS customers_supported,
        SUM(i.total)                             AS total_revenue,
        RANK() OVER (ORDER BY SUM(i.total) DESC) AS employee_rank
    FROM employee e
    JOIN customer c ON c.support_rep_id = e.employee_id
    JOIN invoice  i ON i.customer_id    = c.customer_id
    GROUP BY e.employee_id, e.first_name, e.last_name, e.title
)

-- Stage-by-stage preview (Please uncomment one at a time in pgAdmin)

-- Task 1:
-- SELECT * 
-- FROM customer_profile 
-- ORDER BY total_spent DESC;

-- Task 2: 
-- SELECT * 
-- FROM customer_segments 
-- ORDER BY 
-- CASE 
-- 	WHEN customer_segment = 'Platinum' THEN 1
-- 	WHEN customer_segment = 'Gold' THEN 2
-- 	WHEN customer_segment = 'Silver' THEN 3
-- 	ELSE 4
-- END,
-- total_spent DESC;

-- Task 3: 
-- SELECT * 
-- FROM customer_marketing_plan 
-- ORDER BY customer_segment, total_spent DESC

-- Task 4: 
-- SELECT *
-- FROM country_expansion_score 
-- ORDER BY country_rank;

-- Task 5: final executive report, built entirely from the CTEs above
/*SELECT report_stage, label, detail, metric_name, metric_value
FROM (
    -- 1. Customer Segment Summary
    SELECT 1 AS stage_order, 'Segment Summary' AS report_stage, customer_segment AS label,
           NULL::text AS detail, 'Customers' AS metric_name,
           COUNT(*)::numeric AS metric_value, MIN(loyalty_points) AS sort_key
    FROM customer_segments
    GROUP BY customer_segment

    UNION ALL
    -- 2. Revenue by Segment
    SELECT 2, 'Revenue by Segment', customer_segment, NULL,
           'Revenue ($)', ROUND(SUM(total_spent), 2), MIN(loyalty_points)
    FROM customer_segments
    GROUP BY customer_segment

    UNION ALL
    -- 3. Top Customer in each Segment
    SELECT 3, 'Top Customer per Segment', full_name, customer_segment,
           'Total Spent ($)', ROUND(total_spent, 2), loyalty_points
    FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY customer_segment ORDER BY loyalty_points DESC, total_spent DESC
        ) AS rn
        FROM customer_segments
    ) ranked_customers
    WHERE rn = 1

    UNION ALL
    -- 4. Top Genre in each Segment
    SELECT 4, 'Top Genre per Segment', top_genre, customer_segment,
           'Fans in Segment', fans_in_segment::numeric,
           CASE customer_segment
               WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2
               WHEN 'Silver'  THEN 3 ELSE 4
           END
    FROM segment_top_genre

    UNION ALL
    -- 5. Best Performing Country
    SELECT 5, 'Best Performing Country', country, 'Rank #' || country_rank,
           'Expansion Score', expansion_score, 1
    FROM country_expansion_score
    WHERE country_rank = 1

    UNION ALL
    -- 6. Revenue Contribution by Country (top 5 only, filtered below)
    SELECT 6, 'Revenue by Country ', country, NULL,
           '% of Total Revenue',
           ROUND(100 * total_revenue / SUM(total_revenue) OVER (), 1),
           RANK() OVER (ORDER BY total_revenue DESC)
    FROM country_expansion_score

    UNION ALL
    -- 7. Top Employee by Revenue
    SELECT 7, 'Top Employee by Revenue', employee_name, title,
           'Revenue ($)', ROUND(total_revenue, 2), 1
    FROM employee_leaderboard
    WHERE employee_rank = 1

    UNION ALL
    -- 8. Top Artist by Revenue
    SELECT 8, 'Top Artist by Revenue', artist_name, NULL,
           'Revenue ($)', ROUND(total_revenue, 2), 1
    FROM artist_leaderboard
    WHERE artist_rank = 1

    UNION ALL
    -- 9. Top Album by Revenue
    SELECT 9, 'Top Album by Revenue', album_title, artist_name,
           'Revenue ($)', ROUND(total_revenue, 2), 1
    FROM album_leaderboard
    WHERE album_rank = 1
) executive_dashboard
ORDER BY stage_order, sort_key, metric_value DESC;*/