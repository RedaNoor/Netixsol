# Enterprise Analytics Hackathon

**Author:** Rida Noor

## Database Overview

The source database is AdventureWorks, an enterprise OLTP (transaction-optimized) database with 68 tables spread across five raw operational schemas:

- `person`: names, addresses, contact details
- `humanresources`: employees, departments, pay history
- `production`: products, categories, inventory, bill of materials
- `purchasing`: vendors, purchase orders
- `sales`: customers, sales orders, salespeople, territories

This structure is good for recording one transaction at a time. It is not good for answering business questions, since every question requires joining several of these tables and recalculating the same numbers repeatedly. That is the exact problem this project solves.

## Analytics Architecture

The pipeline follows a layered, dependency-chained design so no metric is ever calculated twice:

```
Raw tables (person / humanresources / production / purchasing / sales)
        |
Stage 1: analytics schema  ->  one MATERIALIZED VIEW per business domain
        |
Stage 2: kpi schema        ->  dashboard-ready metrics, built only on Stage 1
        |
Stage 3: kpi.vw_executive_summary  ->  single roll-up view for leadership
        |
Python notebook (executive_analysis.ipynb)  ->  reads only analytics/kpi views
```

Two new schemas hold the analytics layer, kept separate from the five raw operational schemas so it is always obvious which objects are safe, pre-aggregated, dashboard-ready data:

- `analytics`: Stage 1 domain-level **materialized** views
- `kpi`: Stage 2 and Stage 3 business-metric and executive views (plain views, built on the materialized Stage 1 data)

**Why materialized views, not plain views:** a plain view is just a saved `SELECT` — every downstream query still re-runs the full raw-table join underneath it. That defeats the goal of not repeatedly hitting the operational tables. Stage 1 is materialized so the raw-table joins run once per refresh; all 18 Stage 2/3 views (and the notebook) then read pre-computed rows. Measured effect on this dataset: `kpi.vw_customer_segments` dropped from ~250ms to ~7ms per query once its base view was materialized.

## Intermediate Tables/Views Created

**Stage 1 (`analytics` schema, MATERIALIZED VIEWs), built directly on raw tables:**

| View | Domain | Grain |
|---|---|---|
| `vw_sales_line_analytics` | Sales | one row per order line |
| `vw_customer_analytics` | Customer | one row per customer (customers with ≥1 Shipped order) |
| `vw_product_analytics` | Product | one row per product |
| `vw_employee_analytics` | Employee | one row per salesperson |
| `vw_territory_analytics` | Territory | one row per territory |
| `vw_inventory_analytics` | Inventory | one row per product |
| `vw_purchase_line_analytics` | Purchasing | one row per PO line |
| `vw_vendor_analytics` | Vendor | one row per vendor |

**Stage 2 (`kpi` schema, plain views), built only on Stage 1:**

- Sales: `vw_monthly_revenue`, `vw_quarterly_revenue`, `vw_best_worst_products`
- Customers: `vw_customer_segments`, `vw_customer_ltv`, `vw_customer_retention`
- Products: `vw_product_profitability`, `vw_category_performance`, `vw_product_rankings`
- Employees: `vw_salesperson_rankings`, `vw_employee_revenue_contribution`
- Territories: `vw_regional_revenue`, `vw_regional_growth`
- Inventory/Purchasing: `vw_inventory_health`, `vw_low_stock_products`, `vw_supplier_performance`, `vw_purchasing_trends`

**Stage 3:** `kpi.vw_executive_summary` — a single roll-up view combining headline figures from every Stage 2 view above.

That is **26 reusable views/materialized views across 7 business domains** (Sales, Customer, Product, Employee, Territory, Inventory, Vendor/Purchasing) — well past the brief's minimum of 10 views across 5 domains — and every Stage 2/3 view reuses a Stage 1 view rather than re-joining raw tables.

## SQL Design Decisions

- **`vw_sales_line_analytics` is the single source of truth for revenue, cost, and margin.** `LineTotal` was a SQL Server computed column dropped from `salesorderdetail` after the CSV import, so it is recreated once here as `orderqty * unitprice * (1 - unitpricediscount)`. Every Sales, Customer, Product, Employee, and Territory view reads from this one view instead of recalculating that formula.
- **`vw_purchase_line_analytics` is the purchasing-side counterpart**, factored out so `vw_vendor_analytics` and `vw_purchasing_trends` both reuse the same PO/line join instead of each re-deriving `line_total`/`on_time_flag` independently.
- **Stage 1 is materialized, Stage 2/3 are plain views.** This is the single biggest performance decision in the pipeline (see Analytics Architecture above). A `REFRESH MATERIALIZED VIEW` maintenance block is included at the bottom of `analytics_pipeline.sql` — run it after any new raw data load, since materialized data does not auto-update the way a plain view does.
- **Only `status = 5` (Shipped) orders are counted as revenue.** This excludes cancelled, rejected, and in-process orders so the KPIs reflect completed, revenue-recognized sales rather than pipeline.
- **`pct_of_quota` sums all periods from `salespersonquotahistory`, not `sales.salesperson.salesquota`.** The latter is a single current-quarter snapshot; `total_revenue` is summed across the rep's entire multi-year order history. Dividing multi-year revenue by one quarter's quota was inflating attainment by 10-40x (e.g. reported 4146% instead of the real ~88%). `analytics.vw_employee_analytics` now exposes both `current_period_quota` and `cumulative_quota` so the distinction stays visible.
- **`vw_customer_analytics` only includes customers who have placed a Shipped order.** COUNT(*) against it is "purchasing customers," not every row in `sales.customer`. `kpi.vw_executive_summary` exposes both `total_purchasing_customers` and `total_registered_customers` explicitly so this distinction isn't hidden behind one ambiguous column.
- **Current `standardcost` and `listprice` are used for margin, not historical cost/price tables.** `productcosthistory` and `productlistpricehistory` exist but add significant complexity for a marginal accuracy gain at this stage; this is a documented simplification, not an oversight.
- **RFM customer segmentation uses the data's own max order date as "today,"** not the real current date, since the dataset stops in the past. Using wall-clock time would make every customer look inactive.
- **Advanced SQL techniques used across the pipeline:** chained CTEs (`vw_customer_segments`, `vw_executive_summary`), window functions (`LAG`, `RANK`, `DENSE_RANK`, `ROW_NUMBER`, `NTILE`, `SUM() OVER()`), `CASE WHEN` business logic (stock status, RFM segment labels), conditional aggregation (`SUM(CASE WHEN ...)` for retention rate and on-time delivery), and multi-table joins handling nullable foreign keys (a customer is either an individual `person` or a `store`, joined with `LEFT JOIN` and `COALESCE`).

## Challenges Faced

- Several raw tables had computed columns (`LineTotal`, `TotalDue`, `StockedQty`) removed after the CSV import since they were SQL Server-only computed columns. These had to be recreated manually in the analytics layer using the original formulas.
- `sales.customer` can represent either an individual or a store, with `personid` or `storeid` being null depending on which. Every view that needs a customer name has to branch on this with a `CASE WHEN` and two separate `LEFT JOIN`s.
- Not every product has a `productsubcategoryid` (raw materials and components do not). These were handled with `LEFT JOIN` and `COALESCE(..., 'Uncategorized')` rather than being silently dropped from the product analytics.
- Plain views on top of plain views meant every notebook query re-ran the same raw-table joins repeatedly. Switching Stage 1 to `MATERIALIZED VIEW` fixed this but required adding explicit indexes and a refresh step that a plain view never needed.

## Assumptions Made

- "Completed sale" means `salesorderheader.status = 5`.
- Margin is calculated against current standard cost, not the cost in effect at the time of each historical sale.
- A customer counts as "repeat" if they have more than one distinct `salesorderid` in the Shipped-status dataset.
- Vendor on-time delivery is measured by comparing the purchase order's `shipdate` against each line's `duedate`.
- The source data's most recent month is a **partial month** (orders stop mid-month), not a complete calendar month. `kpi.vw_executive_summary.latest_month_order_count` is exposed specifically so this is visible — the raw `latest_month_growth_pct` should not be read as a real month-over-month decline without checking that count first.

## How to Run This Project

1. Import the raw CSVs using `install.sql` (already Postgres-ready, run through `psql`, not pgAdmin's Query Tool, since it uses `\copy`).
2. Run `analytics_pipeline.sql` against the same database to build the `analytics` and `kpi` schemas.
3. Open `executive_analysis.ipynb`, update the four database connection variables at the top, and run all cells.
4. Fill in the bracketed placeholders in the Executive Recommendations section with the real numbers your run produces.
5. After any future raw data reload, re-run the `REFRESH MATERIALIZED VIEW` block at the bottom of `analytics_pipeline.sql` (or re-run the whole script) — Stage 1 will not update on its own.