"""
Decides whether a question needs structured retrieval (SQL) or semantic
retrieval (pgvector), and calls the right one.
"""

from sql_retriever import search_properties
from rag_pipeline import retrieve as semantic_retrieve

STRUCTURED_TERMS = [
    "price", "cost", "budget", "available", "availability",
    "bedroom", "bedrooms", "size", "square feet", "plot",
    "agent", "developer", "payment",
]


def is_structured_query(query):
    q = query.lower()
    return any(term in q for term in STRUCTURED_TERMS)


def retrieve(query, **filters):
    if filters or is_structured_query(query):
        return {"mode": "structured", "results": search_properties(**filters)}
    return {"mode": "semantic", "results": semantic_retrieve(query)}
