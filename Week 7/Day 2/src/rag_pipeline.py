"""
RAG pipeline built on pgvector.

Documents are split into overlapping chunks, embedded with a local
sentence-transformer model, and stored as rows in the document_chunks
table. Retrieval is a straight cosine-distance query against that table,
so it scales the same way the rest of the knowledge base does, no separate
vector database to run or back up.
"""

from db import get_session, DocumentChunk
from data_loader import load_documents
from embeddings import embed_texts, embed_query


def chunk_text(text, chunk_size=500, overlap=100):
    """Character-based chunking. Simple, predictable, and dependency-light."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def build_index(chunk_size=500, overlap=100, batch_size=64):
    """
    Chunks every source document, embeds the chunks, and writes them into
    document_chunks. Existing chunks are cleared first so this is safe to
    re-run whenever the source documents change.
    """
    documents = load_documents()
    records = []
    for doc in documents:
        for i, chunk in enumerate(chunk_text(doc["text"], chunk_size, overlap)):
            records.append({"source": doc["source"], "chunk_id": i, "text": chunk})

    session = get_session()
    try:
        session.query(DocumentChunk).delete()
        session.commit()

        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]
            vectors = embed_texts([r["text"] for r in batch])
            for record, vector in zip(batch, vectors):
                session.add(DocumentChunk(
                    source=record["source"],
                    chunk_id=record["chunk_id"],
                    text=record["text"],
                    embedding=vector,
                ))
        session.commit()
    finally:
        session.close()

    return len(records)


def retrieve(query, k=3):
    """
    Returns the k most semantically similar chunks to the query, using
    pgvector's cosine distance operator (<=>). Lower distance means more
    similar, so we convert it to a 0-1 similarity score for readability.
    """
    query_vector = embed_query(query)
    session = get_session()
    try:
        rows = (
            session.query(
                DocumentChunk.source,
                DocumentChunk.chunk_id,
                DocumentChunk.text,
                DocumentChunk.embedding.cosine_distance(query_vector).label("distance"),
            )
            .order_by("distance")
            .limit(k)
            .all()
        )
    finally:
        session.close()

    return [
        {
            "source": r.source,
            "chunk_id": r.chunk_id,
            "text": r.text,
            "score": round(1 - r.distance, 4),
        }
        for r in rows
    ]


if __name__ == "__main__":
    from db import init_db
    init_db()
    count = build_index()
    print(f"Indexed {count} chunks.\n")

    query = "What amenities are available at Lake View Apartments?"
    print(f"Query: {query}\n")
    for item in retrieve(query):
        print(f"[{item['score']:.3f}] {item['source']} :: {item['text']}\n")
