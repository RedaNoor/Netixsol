"""
Loads the source data (CSV files and faqs.json) into PostgreSQL.

Run this once after `init_db()` has created the tables, and again any time
the CSV files in data/ are updated. It's written to be safe to re-run:
existing rows are cleared before reloading so you don't end up with
duplicates.
"""

from pathlib import Path
import json
import pandas as pd

from db import (
    get_session, Property, Developer, Location, Amenity,
    School, Hospital, PaymentPlan, Faq,
)

ROOT = Path(__file__).resolve().parents[1]


def load_csv(name):
    return pd.read_csv(ROOT / "data" / name)


def load_faqs():
    with open(ROOT / "data" / "faqs.json", encoding="utf-8") as f:
        return json.load(f)


def load_documents():
    """
    Returns the raw text documents (property brochures, developer profiles,
    FAQ documents) that get chunked and embedded for semantic search.
    """
    docs = []
    for folder in ["property_brochures", "developer_profiles", "faq_documents"]:
        path = ROOT / "documents" / folder
        for file in sorted(path.glob("*.txt")):
            docs.append({
                "source": str(file.relative_to(ROOT)),
                "text": file.read_text(encoding="utf-8"),
            })
    return docs


def _reload_table(session, model, rows):
    session.query(model).delete()
    session.bulk_insert_mappings(model, rows)


def load_all_into_db():
    """Populate every structured table from the CSV and JSON source files."""
    session = get_session()
    try:
        properties = load_csv("properties.csv").to_dict(orient="records")
        _reload_table(session, Property, properties)

        developers = load_csv("developers.csv").to_dict(orient="records")
        _reload_table(session, Developer, developers)

        locations = load_csv("locations.csv").to_dict(orient="records")
        _reload_table(session, Location, locations)

        # amenities.csv has no id column, drop the autoincrement id so it's assigned by the db
        amenities = load_csv("amenities.csv").to_dict(orient="records")
        session.query(Amenity).delete()
        session.bulk_insert_mappings(Amenity, amenities)

        schools = load_csv("schools.csv").to_dict(orient="records")
        _reload_table(session, School, schools)

        hospitals = load_csv("hospitals.csv").to_dict(orient="records")
        _reload_table(session, Hospital, hospitals)

        payment_plans = load_csv("payment_plans.csv").to_dict(orient="records")
        _reload_table(session, PaymentPlan, payment_plans)

        faqs = load_faqs()
        session.query(Faq).delete()
        session.bulk_insert_mappings(Faq, faqs)

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    from db import init_db
    init_db()
    load_all_into_db()
    print("Structured data loaded into Postgres.")
