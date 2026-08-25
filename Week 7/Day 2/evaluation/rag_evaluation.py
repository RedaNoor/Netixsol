from pathlib import Path
import sys, json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_pipeline import retrieve


def evaluate_retrieval():
    questions = json.loads((ROOT / "evaluation/test_questions.json").read_text(encoding="utf-8"))
    rows = []
    for q in questions:
        results = retrieve(q["question"], k=3)
        rows.append({
            "id": q["id"],
            "question": q["question"],
            "type": q["type"],
            "top_score": results[0]["score"] if results else None,
            "sources": "; ".join(r["source"] for r in results),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = evaluate_retrieval()
    print(df.to_string(index=False))
    print("\nNOTE: Retrieval accuracy, grounding rate, and hallucination rate require human/LLM claim-level verification.")
    print("Do not report fabricated metrics. Record actual evaluation results in evaluation_report.md.")
