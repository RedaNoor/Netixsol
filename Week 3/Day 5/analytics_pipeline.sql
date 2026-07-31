-- ENTERPRISE ANALYTICS PIPELINE
-- Pipeline: raw tables -> analytics.* (Stage 1) -> kpi.* (Stage 2) -> kpi.vw_executive_summary (Stage 3) -> notebook

-- >>> Stage 0: schemas for the analytics layer
DROP SCHEMA IF EXISTS kpi CASCADE;
DROP SCHEMA IF EXISTS analytics CASCADE;
CREATE SCHEMA analytics;   
CREATE SCHEMA kpi;         

-- >>>STAGE 1A - SALES ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_sales_line_analytics AS
SELECT
    soh.salesorderid,
    soh.orderdate,
    soh.duedate,
    soh.shipdate,
    soh.customerid,
    soh.salespersonid,
    soh.territoryid,
    soh.onlineorderflag,
    soh.status AS order_status,
    sod.salesorderdetailid,
    sod.productid,
    sod.orderqty,
    sod.unitprice,
    sod.unitpricediscount,
    ROUND(sod.orderqty * sod.unitprice * (1 - sod.unitpricediscount), 2) AS line_revenue,
    ROUND(sod.orderqty * p.standardcost, 2)                            AS line_cost,
    ROUND(
        (sod.orderqty * sod.unitprice * (1 - sod.unitpricediscount))
        - (sod.orderqty * p.standardcost)
    , 2)                                                                AS line_margin,
    p.name                                                              AS product_name,
    p.productsubcategoryid
FROM sales.salesorderheader soh
JOIN sales.salesorderdetail sod ON sod.salesorderid = soh.salesorderid
JOIN production.product p       ON p.productid = sod.productid
-- Status 5 = "Shipped" in AdventureWorks, i.e. a completed, revenue-recognized order.
WHERE soh.status = 5;

-- Indexes on the materialized view: every Stage 1B-1E view groups by one of these columns.
CREATE UNIQUE INDEX idx_sla_pk          ON analytics.vw_sales_line_analytics (salesorderdetailid);
CREATE INDEX idx_sla_customerid         ON analytics.vw_sales_line_analytics (customerid);
CREATE INDEX idx_sla_productid          ON analytics.vw_sales_line_analytics (productid);
CREATE INDEX idx_sla_salespersonid      ON analytics.vw_sales_line_analytics (salespersonid);
CREATE INDEX idx_sla_territoryid        ON analytics.vw_sales_line_analytics (territoryid);
CREATE INDEX idx_sla_orderdate          ON analytics.vw_sales_line_analytics (orderdate);


-- >>> STAGE 1B - CUSTOMER ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_customer_analytics AS
WITH customer_orders AS (
    SELECT
        customerid,
        COUNT(DISTINCT salesorderid)   AS total_orders,
        SUM(line_revenue)              AS total_revenue,
        SUM(line_margin)               AS total_margin,
-- Cast to ::date so downstream date arithmetic (last - first) returns a plain integer number of days.
        MIN(orderdate)::date           AS first_order_date,
        MAX(orderdate)::date           AS last_order_date
    FROM analytics.vw_sales_line_analytics
    GROUP BY customerid
)
SELECT
    c.customerid,
    c.territoryid,
    CASE WHEN c.personid IS NOT NULL THEN 'Individual' ELSE 'Store/Reseller' END AS customer_type,
    COALESCE(
        NULLIF(TRIM(pe.firstname || ' ' || pe.lastname), ''),
        st.name,
        'Unknown Customer'
    )                                                                            AS customer_name,
    co.total_orders,
    ROUND(co.total_revenue, 2)                                                   AS total_revenue,
    ROUND(co.total_margin, 2)                                                    AS total_margin,
    ROUND(co.total_revenue / NULLIF(co.total_orders, 0), 2)                      AS avg_order_value,
    co.first_order_date,
    co.last_order_date
FROM sales.customer c
JOIN customer_orders co ON co.customerid = c.customerid
LEFT JOIN person.person pe ON pe.businessentityid = c.personid
LEFT JOIN sales.store st   ON st.businessentityid = c.storeid;

CREATE UNIQUE INDEX idx_ca_pk           ON analytics.vw_customer_analytics (customerid);
CREATE INDEX idx_ca_territoryid         ON analytics.vw_customer_analytics (territoryid);


-- >>> STAGE 1C - PRODUCT ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_product_analytics AS
WITH product_sales AS (
    SELECT
        productid,
        SUM(orderqty)      AS total_qty_sold,
        SUM(line_revenue)  AS total_revenue,
        SUM(line_cost)     AS total_cost,
        SUM(line_margin)   AS total_margin,
        COUNT(DISTINCT salesorderid) AS orders_containing_product
    FROM analytics.vw_sales_line_analytics
    GROUP BY productid
)
SELECT
    p.productid,
    p.name                                              AS product_name,
    COALESCE(cat.name, 'Uncategorized')                 AS category,
    COALESCE(sub.name, 'Uncategorized')                 AS subcategory,
    p.listprice,
    p.standardcost,
    COALESCE(ps.total_qty_sold, 0)                      AS total_qty_sold,
    COALESCE(ROUND(ps.total_revenue, 2), 0)             AS total_revenue,
    COALESCE(ROUND(ps.total_cost, 2), 0)                AS total_cost,
    COALESCE(ROUND(ps.total_margin, 2), 0)              AS total_margin,
    -- Conditional aggregation guard: avoid divide-by-zero for unsold products
    ROUND(
        COALESCE(ps.total_margin, 0) / NULLIF(ps.total_revenue, 0) * 100
    , 2)                                                 AS margin_pct,
    COALESCE(ps.orders_containing_product, 0)           AS orders_containing_product
FROM production.product p
LEFT JOIN production.productsubcategory sub ON sub.productsubcategoryid = p.productsubcategoryid
LEFT JOIN production.productcategory cat    ON cat.productcategoryid = sub.productcategoryid
LEFT JOIN product_sales ps                  ON ps.productid = p.productid;

CREATE UNIQUE INDEX idx_pa_pk ON analytics.vw_product_analytics (productid);

-- >>> STAGE 1D - EMPLOYEE ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_employee_analytics AS
WITH sp_sales AS (
    SELECT
        salespersonid,
        SUM(line_revenue)            AS total_revenue,
        COUNT(DISTINCT salesorderid) AS total_orders
    FROM analytics.vw_sales_line_analytics
    WHERE salespersonid IS NOT NULL
    GROUP BY salespersonid
),
quota_totals AS (
    SELECT
        businessentityid,
        COUNT(*)          AS quota_periods,
        SUM(salesquota)   AS cumulative_quota
    FROM sales.salespersonquotahistory
    GROUP BY businessentityid
)
SELECT
    sp.businessentityid                                   AS salesperson_id,
    pe.firstname || ' ' || pe.lastname                     AS salesperson_name,
    e.jobtitle,
    ter.name                                               AS territory_name,
    sp.salesquota                                          AS current_period_quota,
    qt.quota_periods,
    qt.cumulative_quota,
    sp.bonus,
    sp.commissionpct,
    COALESCE(s.total_revenue, 0)                           AS total_revenue,
    COALESCE(s.total_orders, 0)                            AS total_orders,
    -- Conditional aggregation: quota attainment over the SAME period as total_revenue,
    -- guarded against reps with no quota history (NULL/0 cumulative_quota).
    ROUND(
        COALESCE(s.total_revenue, 0) / NULLIF(qt.cumulative_quota, 0) * 100
    , 2)                                                    AS pct_of_quota
FROM sales.salesperson sp
JOIN humanresources.employee e ON e.businessentityid = sp.businessentityid
JOIN person.person pe          ON pe.businessentityid = sp.businessentityid
LEFT JOIN sales.salesterritory ter ON ter.territoryid = sp.territoryid
LEFT JOIN sp_sales s               ON s.salespersonid = sp.businessentityid
LEFT JOIN quota_totals qt          ON qt.businessentityid = sp.businessentityid;

CREATE UNIQUE INDEX idx_ea_pk ON analytics.vw_employee_analytics (salesperson_id);

-- >>> STAGE 1E - TERRITORY ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_territory_analytics AS
WITH territory_sales AS (
    SELECT
        territoryid,
        SUM(line_revenue)              AS total_revenue,
        COUNT(DISTINCT salesorderid)   AS total_orders,
        COUNT(DISTINCT customerid)     AS total_customers
    FROM analytics.vw_sales_line_analytics
    WHERE territoryid IS NOT NULL
    GROUP BY territoryid
)
SELECT
    t.territoryid,
    t.name         AS territory_name,
    t.countryregioncode,
    COALESCE(ts.total_revenue, 0)    AS total_revenue,
    COALESCE(ts.total_orders, 0)     AS total_orders,
    COALESCE(ts.total_customers, 0)  AS total_customers,
    ROUND(
        COALESCE(ts.total_revenue, 0) / NULLIF(ts.total_orders, 0), 2
    )                                 AS avg_order_value
FROM sales.salesterritory t
LEFT JOIN territory_sales ts ON ts.territoryid = t.territoryid;

CREATE UNIQUE INDEX idx_ta_pk ON analytics.vw_territory_analytics (territoryid);


-- >>> STAGE 1F - INVENTORY ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_inventory_analytics AS
WITH stock AS (
    SELECT productid, SUM(quantity) AS quantity_on_hand
    FROM production.productinventory
    GROUP BY productid
)
SELECT
    p.productid,
    p.name                                  AS product_name,
    COALESCE(st.quantity_on_hand, 0)        AS quantity_on_hand,
    p.safetystocklevel,
    p.reorderpoint,
    -- CASE WHEN: business-readable stock status
    CASE
        WHEN COALESCE(st.quantity_on_hand, 0) = 0                        THEN 'Out of Stock'
        WHEN COALESCE(st.quantity_on_hand, 0) < p.reorderpoint           THEN 'Below Reorder Point'
        WHEN COALESCE(st.quantity_on_hand, 0) < p.safetystocklevel       THEN 'Below Safety Stock'
        ELSE 'Healthy'
    END                                      AS stock_status
FROM production.product p
LEFT JOIN stock st ON st.productid = p.productid
WHERE p.finishedgoodsflag = true;

CREATE UNIQUE INDEX idx_ia_pk ON analytics.vw_inventory_analytics (productid);


-- >>> STAGE 1G - PURCHASE LINE ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_purchase_line_analytics AS
SELECT
    poh.vendorid,
    poh.purchaseorderid,
    poh.orderdate,
    poh.shipdate,
    pod.duedate,
    pod.orderqty,
    pod.receivedqty,
    pod.rejectedqty,
    ROUND(pod.orderqty * pod.unitprice, 2) AS line_total,
    CASE WHEN poh.shipdate IS NOT NULL AND poh.shipdate <= pod.duedate
         THEN 1 ELSE 0 END AS on_time_flag
FROM purchasing.purchaseorderheader poh
JOIN purchasing.purchaseorderdetail pod ON pod.purchaseorderid = poh.purchaseorderid;

CREATE INDEX idx_pla_vendorid  ON analytics.vw_purchase_line_analytics (vendorid);
CREATE INDEX idx_pla_orderdate ON analytics.vw_purchase_line_analytics (orderdate);


-- >>> STAGE 1H - VENDOR ANALYTICS
CREATE MATERIALIZED VIEW analytics.vw_vendor_analytics AS
SELECT
    v.businessentityid                                      AS vendor_id,
    v.name                                                   AS vendor_name,
    v.creditrating,
    v.preferredvendorstatus,
    COUNT(DISTINCT pl.purchaseorderid)                       AS total_purchase_orders,
    ROUND(SUM(pl.line_total), 2)                             AS total_spend,
    ROUND(SUM(pl.rejectedqty) / NULLIF(SUM(pl.orderqty), 0) * 100, 2)   AS reject_rate_pct,
    -- Conditional aggregation: on-time delivery %
    ROUND(SUM(pl.on_time_flag)::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS on_time_delivery_pct
FROM purchasing.vendor v
LEFT JOIN analytics.vw_purchase_line_analytics pl ON pl.vendorid = v.businessentityid
GROUP BY v.businessentityid, v.name, v.creditrating, v.preferredvendorstatus;

CREATE UNIQUE INDEX idx_va_pk ON analytics.vw_vendor_analytics (vendor_id);


-- >>>  TASK 3 - SALES KPIs
-- Sales KPIs
CREATE OR REPLACE VIEW kpi.vw_monthly_revenue AS
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', orderdate)::date AS revenue_month,
        SUM(line_revenue)                     AS revenue,
        COUNT(DISTINCT salesorderid)          AS order_count
    FROM analytics.vw_sales_line_analytics
    GROUP BY 1
)
, with_prev AS (
    SELECT
        revenue_month,
        revenue,
        order_count,
        LAG(revenue) OVER (ORDER BY revenue_month) AS prev_month_revenue
    FROM monthly
)
SELECT
    revenue_month,
    revenue,
    order_count,
    prev_month_revenue,
    ROUND((revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0) * 100, 2) AS mom_growth_pct
FROM with_prev
ORDER BY revenue_month;

-- kpi.vw_quarterly_revenue: quarterly trend + quarter-over-quarter growth
CREATE OR REPLACE VIEW kpi.vw_quarterly_revenue AS
WITH quarterly AS (
    SELECT
        DATE_TRUNC('quarter', orderdate)::date AS revenue_quarter,
        SUM(line_revenue)                       AS revenue,
        COUNT(DISTINCT salesorderid)            AS order_count
    FROM analytics.vw_sales_line_analytics
    GROUP BY 1
)
, with_prev AS (
    SELECT
        revenue_quarter,
        revenue,
        order_count,
        LAG(revenue) OVER (ORDER BY revenue_quarter) AS prev_quarter_revenue
    FROM quarterly
)
SELECT
    revenue_quarter,
    revenue,
    order_count,
    prev_quarter_revenue,
    ROUND((revenue - prev_quarter_revenue) / NULLIF(prev_quarter_revenue, 0) * 100, 2) AS qoq_growth_pct
FROM with_prev
ORDER BY revenue_quarter;

-- kpi.vw_best_worst_products: ranked product performance, built on Stage 1C
-- ADVANCED SQL: RANK() and DENSE_RANK() ranking functions
CREATE OR REPLACE VIEW kpi.vw_best_worst_products AS
SELECT
    productid,
    product_name,
    category,
    total_revenue,
    total_qty_sold,
    RANK()       OVER (ORDER BY total_revenue DESC) AS revenue_rank_best,
    RANK()       OVER (ORDER BY total_revenue ASC)  AS revenue_rank_worst,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_within_category
FROM analytics.vw_product_analytics
WHERE total_qty_sold > 0;   -- only products that have actually sold

-- >>>  TASK 3 - CUSTOMER KPIs
CREATE OR REPLACE VIEW kpi.vw_customer_segments AS
WITH reference_date AS (
    -- The data itself, not wall-clock time, defines "today" for recency,
    -- since AdventureWorks orders stop in the past.
    SELECT MAX(last_order_date) AS as_of_date FROM analytics.vw_customer_analytics
),
rfm_base AS (
    SELECT
        ca.customerid,
        ca.customer_name,
        ca.customer_type,
        (rd.as_of_date - ca.last_order_date)  AS recency_days,
        ca.total_orders                        AS frequency,
        ca.total_revenue                       AS monetary
    FROM analytics.vw_customer_analytics ca
    CROSS JOIN reference_date rd
),
rfm_scored AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,  -- lower recency_days = better = higher score
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)       AS m_score
    FROM rfm_base
)
SELECT
    customerid,
    customer_name,
    customer_type,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    -- CASE WHEN: translate scores into a business-readable segment
    CASE
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
        WHEN f_score >= 3 AND m_score >= 3                  THEN 'Loyal Customers'
        WHEN r_score >= 3 AND f_score <= 2                  THEN 'New/Promising'
        WHEN r_score <= 2 AND f_score >= 3                  THEN 'At Risk'
        ELSE 'Needs Attention'
    END AS customer_segment
FROM rfm_scored;

-- kpi.vw_customer_ltv: lifetime value proxy, built on Stage 1B
CREATE OR REPLACE VIEW kpi.vw_customer_ltv AS
SELECT
    customerid,
    customer_name,
    customer_type,
    total_orders,
    total_revenue         AS lifetime_value,
    total_margin          AS lifetime_margin,
    avg_order_value,
    first_order_date,
    last_order_date,
    (last_order_date - first_order_date)                          AS customer_tenure_days,
    ROUND(
        total_revenue / NULLIF(GREATEST(last_order_date - first_order_date, 1), 0)
    , 2)                                                            AS revenue_per_active_day
FROM analytics.vw_customer_analytics
ORDER BY lifetime_value DESC;

-- kpi.vw_customer_retention: repeat vs one-time customers, built on Stage 1B
-- ADVANCED SQL: conditional aggregation with SUM(CASE WHEN ...)
CREATE OR REPLACE VIEW kpi.vw_customer_retention AS
SELECT
    COUNT(*)                                                   AS total_customers,
    SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END)          AS repeat_customers,
    SUM(CASE WHEN total_orders = 1 THEN 1 ELSE 0 END)          AS one_time_customers,
    ROUND(
        SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END)::numeric
        / NULLIF(COUNT(*), 0) * 100
    , 2)                                                         AS retention_rate_pct
FROM analytics.vw_customer_analytics;

-- >>> TASK 3 - PRODUCT KPIs
-- kpi.vw_product_profitability: margin-focused view, built on Stage 1C
CREATE OR REPLACE VIEW kpi.vw_product_profitability AS
SELECT
    productid,
    product_name,
    category,
    subcategory,
    total_revenue,
    total_cost,
    total_margin,
    margin_pct,
    RANK() OVER (ORDER BY margin_pct DESC) AS profitability_rank
FROM analytics.vw_product_analytics
WHERE total_qty_sold > 0;

-- kpi.vw_category_performance: rollup by category, built on Stage 1C
CREATE OR REPLACE VIEW kpi.vw_category_performance AS
SELECT
    category,
    COUNT(*)                                AS product_count,
    SUM(total_qty_sold)                     AS total_qty_sold,
    ROUND(SUM(total_revenue), 2)            AS total_revenue,
    ROUND(SUM(total_margin), 2)             AS total_margin,
    ROUND(SUM(total_margin) / NULLIF(SUM(total_revenue), 0) * 100, 2) AS category_margin_pct
FROM analytics.vw_product_analytics
GROUP BY category
ORDER BY total_revenue DESC;

-- kpi.vw_product_rankings: overall product leaderboard, built on Stage 1C
-- ADVANCED SQL: ROW_NUMBER() ranking function
CREATE OR REPLACE VIEW kpi.vw_product_rankings AS
SELECT
    ROW_NUMBER() OVER (ORDER BY total_revenue DESC) AS overall_rank,
    productid,
    product_name,
    category,
    total_qty_sold,
    total_revenue,
    margin_pct
FROM analytics.vw_product_analytics
WHERE total_qty_sold > 0;


-- >>> TASK 3 - EMPLOYEE KPIs

-- kpi.vw_salesperson_rankings: built on Stage 1D
CREATE OR REPLACE VIEW kpi.vw_salesperson_rankings AS
SELECT
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
    salesperson_id,
    salesperson_name,
    territory_name,
    total_revenue,
    total_orders,
    cumulative_quota,
    pct_of_quota
FROM analytics.vw_employee_analytics;

-- kpi.vw_employee_revenue_contribution: each rep's % share of total company revenue
-- ADVANCED SQL: SUM() OVER () window aggregate for a running company total
CREATE OR REPLACE VIEW kpi.vw_employee_revenue_contribution AS
SELECT
    salesperson_id,
    salesperson_name,
    total_revenue,
    ROUND(
        total_revenue / NULLIF(SUM(total_revenue) OVER (), 0) * 100
    , 2) AS pct_of_company_revenue
FROM analytics.vw_employee_analytics
ORDER BY total_revenue DESC;


-- >>> TASK 3 - TERRITORY KPIs

-- kpi.vw_regional_revenue: built on Stage 1E
CREATE OR REPLACE VIEW kpi.vw_regional_revenue AS
SELECT
    territoryid,
    territory_name,
    countryregioncode,
    total_revenue,
    total_orders,
    total_customers,
    avg_order_value,
    RANK() OVER (ORDER BY total_revenue DESC) AS territory_rank
FROM analytics.vw_territory_analytics;

-- kpi.vw_regional_growth: year-over-year growth per territory
-- ADVANCED SQL: LAG() partitioned by territory for YoY comparison
CREATE OR REPLACE VIEW kpi.vw_regional_growth AS
WITH yearly AS (
    SELECT
        s.territoryid,
        t.territory_name,
        EXTRACT(YEAR FROM s.orderdate)::int AS sales_year,
        SUM(s.line_revenue) AS revenue
    FROM analytics.vw_sales_line_analytics s
    JOIN analytics.vw_territory_analytics t ON t.territoryid = s.territoryid
    WHERE s.territoryid IS NOT NULL
    GROUP BY s.territoryid, t.territory_name, EXTRACT(YEAR FROM s.orderdate)
), with_prev AS (
    SELECT
        territoryid,
        territory_name,
        sales_year,
        revenue,
        LAG(revenue) OVER (PARTITION BY territoryid ORDER BY sales_year) AS prev_year_revenue
    FROM yearly
)
SELECT
    territoryid,
    territory_name,
    sales_year,
    revenue,
    prev_year_revenue,
    ROUND((revenue - prev_year_revenue) / NULLIF(prev_year_revenue, 0) * 100, 2) AS yoy_growth_pct
FROM with_prev
ORDER BY territory_name, sales_year;

-- >>> TASK 3 - INVENTORY / PURCHASING KPIs

-- kpi.vw_inventory_health: built on Stage 1F
CREATE OR REPLACE VIEW kpi.vw_inventory_health AS
SELECT
    stock_status,
    COUNT(*)              AS product_count,
    SUM(quantity_on_hand)  AS total_units_on_hand
FROM analytics.vw_inventory_analytics
GROUP BY stock_status
ORDER BY product_count DESC;

-- kpi.vw_low_stock_products: actionable reorder list, built on Stage 1F
CREATE OR REPLACE VIEW kpi.vw_low_stock_products AS
SELECT
    productid,
    product_name,
    quantity_on_hand,
    safetystocklevel,
    reorderpoint,
    stock_status
FROM analytics.vw_inventory_analytics
WHERE stock_status IN ('Out of Stock', 'Below Reorder Point')
ORDER BY quantity_on_hand ASC;

-- kpi.vw_supplier_performance: built on Stage 1G
CREATE OR REPLACE VIEW kpi.vw_supplier_performance AS
SELECT
    vendor_id,
    vendor_name,
    creditrating,
    preferredvendorstatus,
    total_purchase_orders,
    total_spend,
    reject_rate_pct,
    on_time_delivery_pct,
    RANK() OVER (ORDER BY on_time_delivery_pct DESC, reject_rate_pct ASC) AS supplier_rank
FROM analytics.vw_vendor_analytics
WHERE total_purchase_orders > 0;

CREATE OR REPLACE VIEW kpi.vw_purchasing_trends AS
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', orderdate)::date AS purchase_month,
        SUM(line_total)                       AS total_spend,
        COUNT(DISTINCT purchaseorderid)       AS po_count,
        ROUND(AVG(on_time_flag)::numeric * 100, 2) AS on_time_delivery_pct
    FROM analytics.vw_purchase_line_analytics
    GROUP BY 1
),
with_prev AS (
    SELECT
        purchase_month,
        total_spend,
        po_count,
        on_time_delivery_pct,
        LAG(total_spend) OVER (ORDER BY purchase_month) AS prev_month_spend
    FROM monthly
)
SELECT
    purchase_month,
    total_spend,
    po_count,
    on_time_delivery_pct,
    prev_month_spend,
    ROUND((total_spend - prev_month_spend) / NULLIF(prev_month_spend, 0) * 100, 2) AS mom_spend_growth_pct
FROM with_prev
ORDER BY purchase_month;

-- >>> STAGE 3 - EXECUTIVE SUMMARY
-- Stage 3: Executive KPI Summary. One row, built entirely from Stage 2 kpi.* views.

CREATE OR REPLACE VIEW kpi.vw_executive_summary AS
WITH latest_month AS (
    SELECT revenue, mom_growth_pct, order_count
    FROM kpi.vw_monthly_revenue
    ORDER BY revenue_month DESC
    LIMIT 1
),
totals AS (
    SELECT
        SUM(total_revenue) AS all_time_revenue,
        SUM(total_margin)  AS all_time_margin,
        COUNT(*)            AS total_purchasing_customers
    FROM analytics.vw_customer_analytics
),
registered_customers AS (
    SELECT COUNT(*) AS total_registered_customers FROM sales.customer
),
top_territory AS (
    SELECT territory_name, total_revenue
    FROM kpi.vw_regional_revenue
    ORDER BY total_revenue DESC
    LIMIT 1
),
top_product AS (
    SELECT product_name, total_revenue
    FROM kpi.vw_product_rankings
    WHERE overall_rank = 1
),
retention AS (
    SELECT retention_rate_pct FROM kpi.vw_customer_retention
)
SELECT
    t.all_time_revenue,
    t.all_time_margin,
    ROUND(t.all_time_margin / NULLIF(t.all_time_revenue, 0) * 100, 2) AS overall_margin_pct,
    t.total_purchasing_customers,
    rc.total_registered_customers,
    lm.revenue        AS latest_month_revenue,
    lm.mom_growth_pct  AS latest_month_growth_pct,
    lm.order_count     AS latest_month_order_count,
    tt.territory_name  AS top_territory,
    tt.total_revenue   AS top_territory_revenue,
    tp.product_name    AS top_product,
    tp.total_revenue   AS top_product_revenue,
    r.retention_rate_pct
FROM totals t
-- LEFT JOIN ON true (not CROSS JOIN): totals always has exactly one row, so if
-- a singleton lookup below returns zero rows, this still returns one row with NULLs.
LEFT JOIN registered_customers rc ON true
LEFT JOIN latest_month lm    ON true
LEFT JOIN top_territory tt   ON true
LEFT JOIN top_product tp     ON true
LEFT JOIN retention r        ON true;

-- Run manually after building the pipeline
-- TASKS 

-- --0. DATABASE SUMMARY
-- SELECT
--     (SELECT COUNT(*) FROM sales.customer) AS customers,
--     (SELECT COUNT(*) FROM sales.salesorderheader) AS sales_orders,
--     (SELECT COUNT(*) FROM sales.salesorderdetail) AS sales_order_lines,
--     (SELECT COUNT(*) FROM production.product) AS products,
--     (SELECT COUNT(*) FROM purchasing.vendor) AS vendors,
--     (SELECT COUNT(*) FROM purchasing.purchaseorderheader) AS purchase_orders,
--     (SELECT COUNT(*) FROM humanresources.employee) AS employees;

--1. Monthly revenue
-- SELECT *
-- FROM kpi.vw_monthly_revenue;

-- --2. Best Products
-- SELECT *
-- FROM kpi.vw_best_worst_products
-- ORDER BY revenue_rank_best
-- LIMIT 20;

-- --3. Customer Segments 
-- SELECT *
-- FROM kpi.vw_customer_segments
-- LIMIT 20;

-- --4. Customer Retention
-- SELECT *
-- FROM kpi.vw_customer_retention;

-- --5. Product Profitability
-- SELECT *
-- FROM kpi.vw_product_profitability
-- ORDER BY profitability_rank
-- LIMIT 20;

-- --6. Product Rankings
-- SELECT *
-- FROM kpi.vw_product_rankings
-- LIMIT 20;

-- --7. Salesperson Rankings
-- SELECT *
-- FROM kpi.vw_salesperson_rankings;

-- --8. Employee Revenue Contribution
-- SELECT *
-- FROM kpi.vw_employee_revenue_contribution;

-- --9. Regional Revenue
-- SELECT *
-- FROM kpi.vw_regional_revenue;


-- --10. Regional Growth
-- SELECT *
-- FROM kpi.vw_regional_growth;

-- --11. Inventory Health
-- SELECT *
-- FROM kpi.vw_inventory_health;

-- --12. Low Stock Products
-- SELECT *
-- FROM kpi.vw_low_stock_products;

-- --13. Supplier Performance
-- SELECT *
-- FROM kpi.vw_supplier_performance;

-- --14. Purchasing Trends
-- SELECT *
-- FROM kpi.vw_purchasing_trends;

-- --15. Executive Summary
-- SELECT *
-- FROM kpi.vw_executive_summary;

-- Highlights
-- SELECT COUNT(*) FROM analytics.vw_sales_line_analytics;   -- should be > 0
-- SELECT * FROM kpi.vw_low_stock_products LIMIT 10;
-- SELECT * FROM kpi.vw_customer_segments LIMIT 10;

-- MAINTENANCE: refresh the materialized Stage 1 layer after raw data changes.

-- REFRESH MATERIALIZED VIEW analytics.vw_sales_line_analytics;
-- REFRESH MATERIALIZED VIEW analytics.vw_purchase_line_analytics;
-- REFRESH MATERIALIZED VIEW analytics.vw_customer_analytics;
-- REFRESH MATERIALIZED VIEW analytics.vw_product_analytics;
-- REFRESH MATERIALIZED VIEW analytics.vw_employee_analytics;
-- REFRESH MATERIALIZED VIEW analytics.vw_territory_analytics;
-- REFRESH MATERIALIZED VIEW analytics.vw_inventory_analytics;
-- REFRESH MATERIALIZED VIEW analytics.vw_vendor_analytics;
