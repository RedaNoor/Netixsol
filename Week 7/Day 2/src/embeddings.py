"""
Local, free text embeddings using sentence-transformers.

No API key and no per-call cost, the model downloads once and then runs on
CPU. This keeps the RAG pipeline usable during development without needing
an OpenAI or other paid embeddings key, and it's a genuine production
option for a catalog this size.
"""

from functools import lru_cache

from config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts):
    """Embed a list of strings, returns a list of float lists."""
    model = get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def embed_query(text):
    """Embed a single query string."""
    return embed_texts([text])[0]
