# Week 3 Day 4: Music Store Business Intelligence Pipeline

A chained SQL pipeline against the Music Store (PostgreSQL) database that builds
customer profiles, segments customers, recommends campaigns, scores countries
for expansion, and rolls everything into one executive report with every
stage reading from the CTE before it instead of re-querying raw tables.

```
customer_profile
      |
customer_segments  (Task 2)
      |
customer_marketing_plan  (Task 3)
      |
country_expansion_score  (Task 4, reuses customer_segments)
      |
executive dashboard  (Task 5, reuses everything above)
```

## Task 1: Customer Profile

Split into two CTEs before combining them:

- `customer_invoice_summary` money-side numbers (spend, invoice count, avg invoice, active months), grouped straight from `invoice`.
- `customer_catalog_summary` catalog-side numbers (tracks bought, unique genres, unique artists), grouped from `invoice_line`/`track`/`album`.

They're kept apart on purpose. If you join `invoice` to `invoice_line` first and then aggregate everything in one GROUP BY, `total_spent` and `total_invoices` get inflated, every invoice total gets repeated once per track line on that invoice before the SUM ever runs. Aggregating each side separately, then joining two already-aggregated tables, avoids that.


## Task 2: Customer Segmentation

### Logic

Rather than blending spend, frequency, and diversity into a single number and then splitting that number into quartiles, each habit is ranked into quartiles **on its own** first:

- Spend quartile (`NTILE(4)` on total_spent)
- Frequency quartile (`NTILE(4)` on total_invoices)
- Genre-variety quartile (`NTILE(4)` on unique_genres)
- Artist-variety quartile (`NTILE(4)` on unique_artists)

Each quartile converts to points (5 - quartile, so being in the top 25% on a habit scores 4 points, bottom 25% scores 1), spend is weighted double since it's the most direct value signal, and the four point totals are summed into `loyalty_points` (range: 5 to 20). `CASE WHEN` then buckets that range:

| loyalty_points | Segment |
|---|---|
| 16 – 20 | Platinum |
| 11 – 15 | Gold |
| 7 – 10  | Silver |
| 5 – 6   | Bronze |

### Why this instead of one blended formula

A customer who spends a lot but only ever buys one genre from one artist, and a customer who spends moderately but explores widely, land in different places under this system instead of one masking the other inside a single ratio. It also means each factor's contribution is visible in the output (`spend_points`, `frequency_points`, etc.), which is easier to defend in a review than an opaque weighted average.


## Task 3: Marketing Recommendation

Favorite genre is found with `ROW_NUMBER()`, partitioned by customer, ordered by tracks bought per genre (ties broken alphabetically so the result is always deterministic, not dependent on row order). That's joined to the Task 2 segment, and `CASE WHEN` assigns the campaign:

| Segment | Campaign |
|---|---|
| Platinum | Early access to new releases |
| Gold | Curated album bundle offer |
| Silver | Discount on their favorite genre |
| Bronze | Welcome coupon on first purchase |


## Task 4: Country Expansion Strategy

### Methodology

Six metrics, each normalized to 0–1 by dividing by the country with the highest value, then combined into a weighted `expansion_score`:

```
expansion_score = 0.30 × norm(avg_revenue_per_customer)
                + 0.25 × norm(total_revenue)
                + 0.15 × norm(total_customers)
                + 0.10 × norm(avg_invoice_value)
                + 0.10 × norm(genres_purchased)
                + 0.10 × norm(customer_diversity)
```

Two of these needed their own definitions since the brief lists them as separate metrics:

- **genres_purchased**  `COUNT(DISTINCT genre_id)` bought by the *whole country*, a true market-wide catalog-breadth number.
- **customer_diversity**  `COUNT(DISTINCT customer_segment)` present in that country (from Task 2), i.e. whether the country's customer base already spans Bronze through Platinum, or is concentrated in one tier. This is deliberately different from `total_customers` (a headcount) a country could have 20 customers who are all Bronze, or 5 customers spread across all four tiers; the second is arguably the more promising market to expand into.

Revenue-per-customer and total revenue get the heaviest weight because they're proven value, not potential. The other four stop a single high-spending customer in a tiny market from outranking a real, broad one.

### Top 3 recommendation

Run `SELECT * FROM country_expansion_score ORDER BY country_rank;` after loading the data to get the exact ranked list for your dataset. In general, expect the countries with both a sizeable customer base *and* strong revenue per customer to lead, a country with just one or two customers can post a very high average-revenue-per-customer purely from a small sample, which is exactly why `total_customers` and `customer_diversity` are also weighted into the score instead of ranking on revenue-per-customer alone.


## Task 5: Executive Report

One final `UNION ALL` query pulling: segment summary, revenue by segment, top customer/genre per segment, best-performing country, top-5 countries by revenue share, top employee, top artist, and top album — each section from a CTE already built in Tasks 1–4.


## Actionable Recommendations

1. Prioritize expansion spend on countries ranked in the top 3 of `country_expansion_score` — they've proven both revenue depth and a broad customer base, not just a lucky average.
2. Launch the Silver-tier genre discount campaign first: it's usually the largest addressable group sitting just below Gold.
3. Protect the Platinum tier's early-access perk as a retention lever — losing a Platinum customer costs more than losing several Bronze ones.
4. For countries with high revenue-per-customer but low `customer_diversity` (concentrated in one segment), pilot a small campaign before committing a full expansion budget, the market may not be as broad as the headline number suggests.
5. Re-run the segmentation pipeline quarterly. Quartile boundaries and loyalty-point thresholds shift as buying habits change, so a customer's tier should be refreshed, not fixed for life.


## Challenges Faced & How They Were Solved

1. **Joining invoice-level and track-level data in one step inflated the totals.** Fixed by aggregating each side into its own CTE first, then joining two already-summarized tables.
2. **Postgres integer division.** `COUNT()` returns `bigint`, and `bigint / bigint` truncates to `0` or `1` instead of a decimal. Every normalization ratio explicitly casts the numerator to `::numeric` to avoid this.
3. **"Genres Purchased" and "Customer Diversity" could easily become the same number if defined carelessly.** Solved by giving them genuinely different sources: one is a raw catalog-breadth count, the other reuses the segment tiers from Task 2.
4. **NTILE ties.** Customers with identical values on a metric can land in different quartiles depending on tie-breaking, since `NTILE(4) ORDER BY total_spent DESC` alone doesn't guarantee a unique order. This is an accepted limitation for this dataset size; a stricter fix would add a secondary `ORDER BY customer_id` for full determinism.
5. **Keeping nine tasks readable as one script instead of nine disconnected queries.** Solved by strict one-directional dependency: no CTE below Task 1 touches a raw table that an earlier CTE already summarized.


## Skills Demonstrated

- Multi-level, chained CTEs with strict one-way dependency
- Window functions: `NTILE`, `ROW_NUMBER`, `RANK`
- `CASE WHEN`-driven segmentation and conditional labeling
- Weighted, normalized business scoring across metrics of different scales
- Awareness of PostgreSQL numeric/bigint division behavior
- SQL pipeline organization and documentation
