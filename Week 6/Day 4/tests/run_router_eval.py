"""
Runs the router node (in isolation, not the full graph) against the Task 2 test set and writes
an accuracy table, including a per-category breakdown and a confusion log for misroutes.

Run: python tests/run_router_eval.py
Output: reports/router_accuracy.csv, reports/router_accuracy_summary.md
"""
import sys
import csv
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import nodes
from tests.router_eval_prompts import ROUTER_TEST_CASES

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def run_eval():
    rows = []
    for case in ROUTER_TEST_CASES:
        state = {"messages": [], "user_query": case["query"]}
        ingest_update = nodes.ingest_node(state)
        state["messages"] = ingest_update["messages"]

        result = nodes.router_node(state)
        predicted = result["intent"]
        correct = predicted == case["expected"]

        rows.append({
            "id": case["id"], "query": case["query"], "expected": case["expected"],
            "predicted": predicted, "correct": correct,
            "confidence": result["router_confidence"], "reasoning": result["router_reasoning"],
        })
        print(f"[{case['id']}] {'OK ' if correct else 'MISS'} expected={case['expected']:18s} "
              f"predicted={predicted:18s} conf={result['router_confidence']:.2f}")

    with open(REPORTS_DIR / "router_accuracy.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    write_summary(rows)
    return rows


def write_summary(rows):
    total = len(rows)
    correct = sum(r["correct"] for r in rows)
    by_category = defaultdict(lambda: {"correct": 0, "total": 0})
    misroutes = []

    for r in rows:
        by_category[r["expected"]]["total"] += 1
        if r["correct"]:
            by_category[r["expected"]]["correct"] += 1
        else:
            misroutes.append(r)

    lines = [
        "# Router Accuracy Summary",
        "",
        f"Overall: {correct}/{total} ({correct/total:.1%})",
        "",
        "## By expected category",
        "",
        "| Category | Correct | Total | Accuracy |",
        "|---|---|---|---|",
    ]
    for cat, stats in sorted(by_category.items()):
        acc = stats["correct"] / stats["total"] if stats["total"] else 0
        lines.append(f"| {cat} | {stats['correct']} | {stats['total']} | {acc:.0%} |")

    lines += ["", "## Misroutes", ""]
    if misroutes:
        lines.append("| id | query | expected | predicted | reasoning |")
        lines.append("|---|---|---|---|---|")
        for m in misroutes:
            lines.append(f"| {m['id']} | {m['query']} | {m['expected']} | {m['predicted']} | {m['reasoning']} |")
        lines += ["", "Fix applied for each pattern (fill in after reviewing reasoning above):", "",
                  "| Misroute pattern | Fix applied to router prompt |", "|---|---|", "| | |"]
    else:
        lines.append("None.")

    with open(REPORTS_DIR / "router_accuracy_summary.md", "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    run_eval()
