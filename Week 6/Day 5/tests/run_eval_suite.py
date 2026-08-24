"""
Runs the combined evaluation suite. prediction_sanity cases execute for real right now (no API
key needed — direct model calls). factual_qa, scope_guardrail, and multiturn_coherence cases go
through the full graph and need a real API key; run this script after filling in .env.

Run: python tests/run_eval_suite.py
Output: reports/eval_results.csv, reports/eval_summary.md
"""
import sys
import csv
import uuid
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import predict
from graph import build_graph
from tests.eval_suite import (FACTUAL_QA_CASES, PREDICTION_SANITY_CASES,
                               SCOPE_GUARDRAIL_CASES, MULTITURN_CONVERSATIONS, BENCHMARK_COMPARISON)

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def run_prediction_sanity():
    """These execute directly against predict.py — real, immediately verifiable, no API key."""
    import pandas as pd
    rows = []
    mf = pd.read_parquet(Path(__file__).parent.parent / "data" / "feature_table_matches_v1.parquet")

    for case in PREDICTION_SANITY_CASES:
        if case["id"] == "p_05":
            r_home = predict.predict_match_winner(case["team_strong"], case["team_weak"], case["date"])
            r_away = predict.predict_match_winner(case["team_weak"], case["team_strong"], case["date"])
            p_strong_home = r_home["probabilities"]["HOME_WIN"]
            p_strong_away = r_away["probabilities"]["AWAY_WIN"]
            passed = p_strong_home > p_strong_away
            detail = f"P(strong wins|home)={p_strong_home:.3f} vs P(strong wins|away)={p_strong_away:.3f}"
        elif case["id"] == "p_06":
            sample = mf[mf.year == 2025].sample(10, random_state=1)
            draw_probs = [predict.predict_match_winner(row["home_team"], row["away_team"],
                                                         str(row["match_date"].date()))["probabilities"]["DRAW"]
                          for _, row in sample.iterrows()]
            passed = max(draw_probs) < 0.05
            detail = f"max_draw_prob={max(draw_probs):.4f} across {len(draw_probs)} matches"
        else:
            r = predict.predict_match_winner(case["home"], case["away"], case["date"])
            home_p, away_p = r["probabilities"]["HOME_WIN"], r["probabilities"]["AWAY_WIN"]
            if case["check"] == "away_win_prob > 0.7":
                passed = away_p > 0.7
            elif case["check"] == "0.5 < home_win_prob < 0.75":
                passed = 0.5 < home_p < 0.75
            else:
                passed = False
            detail = f"home_win={home_p:.3f} away_win={away_p:.3f}"

        rows.append({"id": case["id"], "category": "prediction_sanity",
                      "description": case["description"], "detail": detail, "passed": passed})
        print(f"[{case['id']}] {'PASS' if passed else 'FAIL'} — {case['description']} ({detail})")

    return rows


def run_factual_qa(app):
    rows = []
    for case in FACTUAL_QA_CASES:
        thread_id = f"eval-{case['id']}-{uuid.uuid4().hex[:6]}"
        result = app.invoke({"user_query": case["query"]}, config={"configurable": {"thread_id": thread_id}})
        response = result.get("final_response", "")
        auto_pass = any(kw.lower() in response.lower() for kw in case["check_contains_any"])
        rows.append({"id": case["id"], "category": "factual_qa", "query": case["query"],
                      "response": response, "auto_pass": auto_pass, "manual_pass_fail": ""})
        print(f"[{case['id']}] auto={'PASS' if auto_pass else 'CHECK'} — {case['query']}")
    return rows


def run_scope_guardrails(app):
    rows = []
    for case in SCOPE_GUARDRAIL_CASES:
        thread_id = f"eval-{case['id']}-{uuid.uuid4().hex[:6]}"
        result = app.invoke({"user_query": case["query"]}, config={"configurable": {"thread_id": thread_id}})
        intent = result.get("intent")
        response = result.get("final_response", "")
        auto_pass = intent == case["expected_intent"]
        rows.append({"id": case["id"], "category": "scope_guardrail", "query": case["query"],
                      "expected_intent": case["expected_intent"], "actual_intent": intent,
                      "response": response, "auto_pass": auto_pass, "manual_pass_fail": ""})
        print(f"[{case['id']}] auto={'PASS' if auto_pass else 'FAIL'} — expected={case['expected_intent']} actual={intent}")
    return rows


def run_multiturn(app):
    rows = []
    for convo in MULTITURN_CONVERSATIONS:
        thread_id = f"eval-{convo['id']}-{uuid.uuid4().hex[:6]}"
        config_ = {"configurable": {"thread_id": thread_id}}
        for i, turn in enumerate(convo["turns"]):
            result = app.invoke({"user_query": turn}, config=config_)
            response = result.get("final_response", "")
            rows.append({"id": f"{convo['id']}_turn{i+1}", "category": "multiturn_coherence",
                          "conversation": convo["id"], "turn_number": i + 1, "query": turn,
                          "response": response, "manual_pass_fail": ""})
            print(f"[{convo['id']} turn {i+1}] {turn} -> {response[:80]}")
    return rows


def write_summary(all_rows):
    by_category = defaultdict(lambda: {"pass": 0, "total": 0, "needs_manual": 0})
    for r in all_rows:
        cat = r["category"]
        by_category[cat]["total"] += 1
        if "passed" in r:
            by_category[cat]["pass"] += int(r["passed"])
        elif "auto_pass" in r:
            by_category[cat]["pass"] += int(r["auto_pass"])
            by_category[cat]["needs_manual"] += 1
        else:
            by_category[cat]["needs_manual"] += 1

    lines = ["# Evaluation Summary", "", "| Category | Auto Pass | Total | Auto Pass Rate | Needs Manual Review |",
              "|---|---|---|---|---|"]
    weakest = None
    for cat, stats in sorted(by_category.items()):
        rate = stats["pass"] / stats["total"] if stats["total"] else 0
        lines.append(f"| {cat} | {stats['pass']} | {stats['total']} | {rate:.0%} | {stats['needs_manual']} |")
        if weakest is None or rate < weakest[1]:
            weakest = (cat, rate)

    lines += ["", f"**Weakest category (by automated pass rate): {weakest[0]} ({weakest[1]:.0%})**", "",
              "Categories marked 'Needs Manual Review' > 0 require reading the response column and filling "
              "in manual_pass_fail before treating the automated rate as final — the automated check is a "
              "keyword/intent heuristic, not a real correctness judgment.", "",
              "## Proposed improvement for the weakest category", "",
              "(fill in after reviewing the actual failing cases — see reports/eval_results.csv)", "",
              "## Benchmark comparison: match-winner model vs. naive ladder-position baseline", "",
              BENCHMARK_COMPARISON["description"], "",
              "| Season | Model Accuracy | Ladder Baseline Accuracy |", "|---|---|---|"]
    for r in BENCHMARK_COMPARISON["results"]:
        lines.append(f"| {r['year']} | {r['model_accuracy']:.1%} | {r['ladder_baseline_accuracy']:.1%} |")
    lines += ["", f"Always-home baseline (2025, for reference): {BENCHMARK_COMPARISON['always_home_baseline_2025']:.1%}",
              "", BENCHMARK_COMPARISON["note"]]

    with open(REPORTS_DIR / "eval_summary.md", "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


def main():
    print("=== Prediction sanity (executed directly, no API key needed) ===")
    prediction_rows = run_prediction_sanity()

    app = build_graph()
    print("\n=== Factual QA ===")
    factual_rows = run_factual_qa(app)
    print("\n=== Scope guardrails ===")
    scope_rows = run_scope_guardrails(app)
    print("\n=== Multi-turn coherence ===")
    multiturn_rows = run_multiturn(app)

    all_rows = prediction_rows + factual_rows + scope_rows + multiturn_rows
    fieldnames = sorted({k for r in all_rows for k in r.keys()})
    with open(REPORTS_DIR / "eval_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_rows:
            writer.writerow(r)

    write_summary(all_rows)
    print(f"\nWritten to {REPORTS_DIR}/eval_results.csv and eval_summary.md")


if __name__ == "__main__":
    main()
