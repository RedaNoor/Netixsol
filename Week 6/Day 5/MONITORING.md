---
noteId: "3ff8f2b09f9111f1be04e92091ab93e6"
tags: []

---

# AFL Assistant — Monitoring & Maintenance Checklist

## What to track (from the structured JSON logs in `logging_setup.py`)

| Metric | Source | Alert threshold | Cadence |
|---|---|---|---|
| **Response latency (p50/p95)** | `latency_ms` per request | p95 > 8s sustained for 15 min | Real-time dashboard, reviewed daily |
| **Tool error rate** | `tool_error` non-null / total requests | > 5% over any rolling 1-hour window | Real-time alert |
| **Timeout rate** | `ToolTimeoutError` occurrences in logs | > 2% of requests | Real-time alert |
| **Off-topic leak rate** | Manual/automated audit of a response sample where `intent="off_topic"` but the response text engages with the off-topic content | > 1% in a weekly audit sample of 50 | Weekly |
| **Router misclassification rate** | Re-running `tests/run_router_eval.py` against the fixed 20-case set | Accuracy drops below 85% (baseline established at launch) | Weekly, or after any prompt change |
| **Clarification rate** | `needs_clarification=True` / total requests | Sudden jump (>2x week-over-week) — signals a naming/entity-resolution gap, not necessarily bad on its own | Weekly |
| **Prediction accuracy drift** | Compare `predict_match_winner` output against actual results as each round completes | Rolling 5-round accuracy drops more than 8 points below the Day 2 holdout baseline (~70%) | After every completed round |
| **Rate-limit hits (429s)** | API access logs | Sudden spike from a single `conversation_id` — possible abuse/scraping | Real-time alert |
| **Token usage / cost** | `token_usage` per request (when the provider reports it) | Daily spend exceeds budget threshold (set per deployment) | Daily |

## Weekly retraining / data-refresh loop

1. **After each round completes** (new match results now finalized): append the new
   `team_matches_home_away_raw.csv` / `afl_players_round_by_round_stats_raw.csv` rows for that
   round to the raw data store.
2. **Re-run the Day 1 feature pipeline** (`pipeline.py` logic) against the updated raw data —
   this regenerates `feature_table_matches_v1.parquet` and `feature_table_players_v1.parquet`
   with the new round's results folded into rolling form, ladder position, and head-to-head
   features for every team going forward. This step is cheap (minutes, not hours) since it's
   the same deterministic pandas pipeline from Day 1, not a training run.
3. **Score the just-completed round retrospectively**: for every match in the round that just
   finished, compare what `predict_match_winner` would have said *before* the round (using data
   as of the prior round) against the actual result. Log this to a rolling accuracy tracker —
   this is the concrete input to the "prediction accuracy drift" metric above.
4. **Retrain trigger, not a fixed calendar**: don't retrain every week by default — retrain when
   either (a) the rolling 5-round accuracy check in step 3 drops below the 8-point drift
   threshold, or (b) a full season boundary passes (new season means a full ladder reset, which
   changes the shape of the ladder-position feature enough to warrant a fresh holdout split), or
   (c) 8+ new rounds of data have accumulated since the last retrain, whichever comes first.
   Retraining every single week for a model that only sees ~9 new matches (one round) is mostly
   just noise — the point of monitoring drift first is to retrain when there's a real reason to,
   not on a fixed clock.
5. **Retraining itself** is the Day 2 notebook re-run end to end against the refreshed feature
   tables, followed by the same walk-forward evaluation against the ladder baseline before the
   new model artifact replaces the one in production — never promote a retrained model without
   re-confirming it still beats the baseline on a genuine held-out set.

## Operational notes

- The router accuracy test set (`tests/router_eval_prompts.py`) and the guardrail eval set
  (`tests/eval_suite.py`) are the two fixed benchmarks to re-run after *any* prompt change to
  `config.py` — a router prompt edit that fixes one misroute can silently break another; the
  fixed test set is what catches that before it reaches production.
- Off-topic leak rate can't be fully automated (see `tests/run_eval_suite.py`'s note on this) —
  budget real human review time for it weekly rather than trusting the keyword heuristic alone.
- The prediction disclaimer (`config.PREDICTION_DISCLAIMER`) is applied structurally in
  `response_formatter_node`, not by prompt instruction — if a future refactor moves formatting
  logic, re-verify this specific guarantee didn't get lost in the move.
