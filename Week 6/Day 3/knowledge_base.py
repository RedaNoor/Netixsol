"""
Semantic retrieval layer.

The dataset has no unstructured text (no match reports, no articles) — it's entirely structured
stats and results. Exact numbers always come from tools.py, never from this layer. What this
layer covers instead is the kind of question a structured lookup handles badly: "which matches
had a really tight finish in 2023" or "find close games between these two teams" — narrative-
shaped questions where semantic similarity over short, factual match descriptions is a better
fit than a rigid SQL-style filter.

Each entry is a short, template-generated description built directly from real match data
(scores, teams, venue, margin) — not free text, not invented commentary. Every fact inside a
description is traceable back to a row in feature_table_matches_v1.parquet.
"""
import pandas as pd
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_INDEX_DIR = Path(__file__).parent / "vector_index"


def _match_description(row) -> str:
    margin = abs(int(row["margin_home"]))
    if row["target_result"] == "DRAW":
        outcome = f"{row['home_team']} and {row['away_team']} drew"
    else:
        winner = row["home_team"] if row["target_result"] == "HOME_WIN" else row["away_team"]
        loser = row["away_team"] if row["target_result"] == "HOME_WIN" else row["home_team"]
        closeness = "a close, low-margin" if margin <= 12 else ("a tight" if margin <= 24 else "a comfortable")
        outcome = f"{winner} beat {loser} by {margin} points in {closeness} finish"
    final = f"{row['home_score']}-{row['away_score']}"
    return (f"{row['home_team']} vs {row['away_team']} at {row['venue']} on "
            f"{row['match_date'].date()} (Round {row['round']}, {row['year']}): {outcome}. "
            f"Final score {final}.")


def build_corpus() -> pd.DataFrame:
    """Build the match-description corpus from the structured match table."""
    matches = pd.read_parquet(_DATA_DIR / "feature_table_matches_v1.parquet")
    matches = matches.dropna(subset=["home_score", "away_score", "venue"])
    matches["description"] = matches.apply(_match_description, axis=1)
    return matches[["match_id", "match_date", "year", "home_team", "away_team", "description"]]


def build_vector_store():
    """
    Build (or load, if already built) a FAISS vector store over the match-description corpus.
    Uses a local sentence-transformer embedding model so this layer has no dependency on
    whichever LLM provider is configured for the chat model.
    """
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_core.documents import Document

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    if _INDEX_DIR.exists():
        return FAISS.load_local(str(_INDEX_DIR), embeddings, allow_dangerous_deserialization=True)

    corpus = build_corpus()
    docs = [
        Document(
            page_content=row["description"],
            metadata={"match_id": row["match_id"], "year": int(row["year"]),
                      "home_team": row["home_team"], "away_team": row["away_team"]},
        )
        for _, row in corpus.iterrows()
    ]
    store = FAISS.from_documents(docs, embeddings)
    store.save_local(str(_INDEX_DIR))
    return store


def search_match_descriptions(query: str, k: int = 5) -> list:
    """
    Semantic search over match descriptions. Returns the k most relevant matches with their
    metadata. Use this for narrative/exploratory questions about matches, not for exact stats.
    """
    store = build_vector_store()
    results = store.similarity_search(query, k=k)
    return [{"description": d.page_content, **d.metadata} for d in results]
