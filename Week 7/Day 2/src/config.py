"""
Central place for configuration values.

Everything here is read from environment variables so the same code works
locally, in Docker, and on whatever host this ends up deployed to. Nothing
in this file is a real credential, they're placeholders meant to be set in
a .env file or in the hosting platform's environment settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file in the project root, if one exists

# Full Postgres connection string. Get this from your Neon (or other
# Postgres + pgvector) project dashboard, for example:
# postgresql+psycopg2://user:password@host/dbname?sslmode=require
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in "
        "your real Postgres connection string before running anything."
    )

# Local, free sentence embedding model. Runs on CPU, no API key needed.
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSIONS = 384  # matches all-MiniLM-L6-v2 output size

# Chunking defaults for the RAG pipeline. Day 2 evaluation compares a few
# alternatives to these numbers.
DEFAULT_CHUNK_SIZE = int(os.environ.get("RAG_CHUNK_SIZE", 500))
DEFAULT_CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", 100))
