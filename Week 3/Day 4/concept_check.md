## Week 3 Day 4: Music Store Business Intelligence Pipeline
### Concept Check

**1. Why are multiple CTEs preferred over one large nested query?**
Nested subqueries force you to read from the inside out, and you can't run just the inner piece on its own to check it — it's welded to everything around it. A CTE is a named, standalone step: you can **SELECT * FROM that_cte** by itself to verify it's correct before building the next stage on top of it. That makes a long pipeline debuggable one stage at a time instead of all at once.

**2. When would you use a window function instead of GROUP BY?**
GROUP BY collapses a table down to one row per group — you lose the individual rows. A window function computes the same kind of aggregate (a rank, a running total, a max) but keeps every original row intact, so you can put "this customer's spend" next to "the top spend in their country" on the same line. Use GROUP BY when you only want the summary; use a window function when you need the summary *alongside* the detail.

**3. Explain the difference between ROW_NUMBER(), RANK(), and DENSE_RANK().**
All three number rows within an ordering, but they disagree on what to do with ties. Say three customers are tied for the 2nd-highest spend:
- **ROW_NUMBER()** ignores the tie and just hands out 1, 2, 3, 4 in some order — no two rows ever share a number.
- **RANK()** gives the tied rows the same number, then skips ahead: 1, 2, 2, 4.
- **DENSE_RANK()** gives the tied rows the same number too, but doesn't skip: 1, 2, 2, 3.
Pick **ROW_NUMBER()** when you need a strict "keep exactly one row per group" filter, **RANK() / DENSE_RANK** when ties should genuinely share a position.

**4. What is conditional aggregation?**
Putting a **CASE WHEN** inside an aggregate function so one pass over the data produces several conditional totals instead of one plain total. For example:
```sql
SUM(CASE WHEN country = 'USA' THEN total ELSE 0 END) AS usa_revenue
```
This turns what would need several separate filtered queries into one query with several output columns.

**5. How does CASE WHEN improve analytical reporting?**
It turns raw numbers into the categories a business actually talks in. A loyalty points value of 17 means nothing to a manager on its own; **CASE WHEN loyalty_points >= 16** THEN 'Platinum' turns it into a label someone can act on immediately.

**6. Why should SQL queries be broken into logical stages?**
A single giant query that computes a customer profile, segments, favorite genres, and a country score all at once is nearly impossible to check for correctness, a mistake anywhere is invisible everywhere. Breaking it into stages means each one has a single, checkable job, later stages don't repeat earlier calculations, and someone reading the query later can follow the logic top to bottom instead of untangling it.

**7. What makes a SQL query maintainable?**
Descriptive CTE and column names, comments that explain *why* a step exists (not just what it does), no duplicated logic between stages, and getting the data types right — a query can read perfectly cleanly and still return wrong numbers if, for example, an integer division silently truncates a ratio to zero. Maintainable also means trustworthy, not just tidy.
