"""
Property recommendation engine.

Exact filters (budget, city, area, bedrooms) are applied in SQL first via
search_properties. This module only ranks the candidates that already
passed those filters, using a simple, transparent scoring formula rather
than a black box, so the reasoning behind a recommendation can always be
explained to a customer or a teammate.
"""

from sql_retriever import search_properties


def recommend(budget, city=None, area=None, bedrooms=None, purpose=None, amenities=None):
    candidates = search_properties(budget=budget, city=city, area=area, bedrooms=bedrooms)

    if not candidates:
        return []

    for c in candidates:
        budget_score = 1 - min(c["price"] / budget, 1) if budget else 0.5
        purpose_score = 1.0 if purpose and c["purpose"] == purpose else (0.5 if not purpose else 0.0)
        c["score"] = round(0.55 * budget_score + 0.25 * purpose_score + 0.20, 4)

    return sorted(candidates, key=lambda c: c["score"], reverse=True)


if __name__ == "__main__":
    for row in recommend(budget=50000000, city="Lahore", bedrooms=3, purpose="Family"):
        print(row["property_id"], row["name"], row["price"], row["score"])
