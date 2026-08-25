
#  Knowledge Base, RAG & Property Intelligence

Production-oriented deliverable for a real-estate AI voice agent.

## Deliverables
1. Knowledge base datasets (medium-sized: 40 properties across 4 cities)
2. RAG pipeline with configurable chunk sizes, backed by pgvector
3. Structured SQL + semantic vector retrieval split, both in the same Postgres database
4. Property recommendation engine
5. 20-question hallucination/grounding evaluation

## Architecture

User Query -> Query Understanding -> Structured SQL / Semantic pgvector Retrieval
-> Retrieved Context -> Grounding Validation -> LLM -> Verified Response

Both the structured tables (properties, developers, locations, amenities, schools,
hospitals, payment plans, FAQs) and the vector store for semantic search live in one
PostgreSQL database, using the pgvector extension for the embedding column. One
database to run and back up, and it also means a single query can combine an exact
SQL filter with a semantic ranking when that's useful.

## Data Policy
The assistant must never invent property facts. If verified evidence is unavailable,
the response should explicitly say that the information is not available in the
knowledge base.

## Setup

Create a free Postgres database at [neon.com](https://neon.com) (no card needed) and
enable the pgvector extension for it, either from Neon's dashboard or by running
`CREATE EXTENSION vector;` once you're connected. Copy the connection string it
gives you.

Copy the environment file and paste in that connection string:

```bash
cp .env.example .env
```

Install dependencies:

```bash
# Windows: .venv\Scripts\activate
# install requirements
pip install -r requirements.txt
```

Load the structured data and build the vector index:

```bash
python src/data_loader.py
python src/rag_pipeline.py
```

`data_loader.py` creates the tables and loads the CSV/JSON files into Postgres.
`rag_pipeline.py` builds the vector index the first time it runs, then prints a
sample query so you can see it working end to end.

Run the rest of the demo:

```bash
python src/recommendation_engine.py
python evaluation/rag_evaluation.py
```

## Embeddings

Semantic search uses `sentence-transformers` (`all-MiniLM-L6-v2` by default) running
locally on CPU. No API key, no per-call cost, and it's a genuine production option
for a catalog this size. Swap `EMBEDDING_MODEL_NAME` in `src/config.py` for a larger
model, or point `embeddings.py` at a hosted API later, if quality needs ever outgrow it.
