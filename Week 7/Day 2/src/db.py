"""
Database layer for the real estate knowledge base.

Everything lives in a single PostgreSQL database: the structured property
tables and the vector store for semantic search both sit here, using the
pgvector extension for the embedding column. That keeps the whole knowledge
base in one place instead of splitting it across a SQL database and a
separate vector database.
"""

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

from config import DATABASE_URL, EMBEDDING_DIMENSIONS

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)
Base = declarative_base()


class Property(Base):
    __tablename__ = "properties"

    property_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    developer = Column(String, nullable=False)
    city = Column(String, nullable=False, index=True)
    area = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    bedrooms = Column(Integer, nullable=False)
    size_sqft = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    purpose = Column(String, nullable=False, index=True)


class Developer(Base):
    __tablename__ = "developers"

    developer_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    projects = Column(Text)
    reputation = Column(Text)


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(String, primary_key=True)
    city = Column(String, nullable=False)
    area = Column(String, nullable=False)
    description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)


class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(String, ForeignKey("properties.property_id"), index=True)
    amenity_name = Column(String, nullable=False)


class School(Base):
    __tablename__ = "schools"

    school_id = Column(String, primary_key=True)
    school_name = Column(String, nullable=False)
    area = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False)
    distance_km = Column(Float)
    rating = Column(Float)


class Hospital(Base):
    __tablename__ = "hospitals"

    hospital_id = Column(String, primary_key=True)
    hospital_name = Column(String, nullable=False)
    area = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False)
    distance_km = Column(Float)
    rating = Column(Float)


class PaymentPlan(Base):
    __tablename__ = "payment_plans"

    plan_id = Column(String, primary_key=True)
    property_id = Column(String, ForeignKey("properties.property_id"), index=True)
    down_payment_percent = Column(Integer)
    installment_months = Column(Integer)
    monthly_installment = Column(Integer)
    notes = Column(Text)


class Faq(Base):
    __tablename__ = "faqs"

    id = Column(String, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, index=True)


class DocumentChunk(Base):
    """
    One row per chunk of a source document (brochure, developer profile,
    FAQ document). This is the table pgvector searches against for
    semantic retrieval.
    """
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False, index=True)
    chunk_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIMENSIONS), nullable=False)


def init_db():
    """Create the pgvector extension and all tables if they don't exist yet."""
    with engine.connect() as conn:
        conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
