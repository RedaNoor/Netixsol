"""
Structured retrieval for exact facts: price, availability, bedrooms,
size, agent/developer names. This goes straight to SQL rather than
semantic search, because these are the kind of facts that need to be
exactly right, not just similar.
"""

from db import get_session, Property


def search_properties(budget=None, city=None, area=None, bedrooms=None, property_type=None):
    session = get_session()
    try:
        query = session.query(Property).filter(Property.status == "Available")

        if budget is not None:
            query = query.filter(Property.price <= budget)
        if city:
            query = query.filter(Property.city == city)
        if area:
            query = query.filter(Property.area == area)
        if bedrooms is not None:
            query = query.filter(Property.bedrooms == bedrooms)
        if property_type:
            query = query.filter(Property.type == property_type)

        results = query.all()
        return [
            {
                "property_id": p.property_id, "name": p.name, "developer": p.developer,
                "city": p.city, "area": p.area, "type": p.type, "bedrooms": p.bedrooms,
                "size_sqft": p.size_sqft, "price": p.price, "status": p.status,
                "purpose": p.purpose,
            }
            for p in results
        ]
    finally:
        session.close()


if __name__ == "__main__":
    for row in search_properties(budget=50000000, city="Lahore", bedrooms=3):
        print(row)
