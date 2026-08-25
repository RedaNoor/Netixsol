---
noteId: "5d99f4d0a07311f195900762b9117099"
tags: []

---

# Knowledge Base Schema

## Why CSV and JSON as source files, Postgres as the runtime store

The CSV and JSON files in this folder are the source of truth, easy to open and
edit by hand in Excel or Google Sheets when the client wants to update prices or
add a property. `data_loader.py` loads them into PostgreSQL, which is what the
running application actually queries. Structured facts (prices, bedrooms,
availability, distances) map directly to SQL tables for exact filtering like
"under 5 crore" or "3 bedroom apartments in Lahore". FAQs started life as JSON
because each entry has a natural nested shape (question, answer, category)
rather than flat rows; they land in a `faqs` table alongside everything else.

## properties.csv (40 rows)
Core property inventory: houses, apartments, commercial units and plots across
Lahore, Islamabad, Rawalpindi and Karachi.

## developers.csv (12 rows)
Developer profiles and the projects associated with each one.

## locations.csv (18 rows)
City and area metadata with descriptions and coordinates.

## amenities.csv (~150 rows)
Property-to-amenity relationships, 3 to 5 amenities per property.

## schools.csv (17 rows)
Nearby school information per area.

## hospitals.csv (17 rows)
Nearby hospital information per area.

## payment_plans.csv (25 rows)
Structured payment-plan values for available properties (plots are excluded,
since those are typically sold outright).

## faqs table (15 rows)
Frequently asked questions and verified answers, grouped by category.
Loaded from `data/faqs.json` into Postgres by `data_loader.py`.

## document_chunks table
Not a source file, this table is built by `rag_pipeline.py`. Each row is one
chunk of a brochure, developer profile, or FAQ document, together with its
embedding vector, stored using the pgvector extension. This is what semantic
search queries against.

## Note on P001 to P008
These eight properties keep the exact same values as the original Day 2
submission, because the evaluation test questions in `evaluation/test_questions.json`
reference them by name and id. P009 onward are new additions.
