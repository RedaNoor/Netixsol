---
noteId: "232289209f9711f1be04e92091ab93e6"
tags: []

---

# Evaluation Summary

| Category | Auto Pass | Total | Auto Pass Rate | Needs Manual Review |
|---|---|---|---|---|
| factual_qa | 6 | 6 | 100% | 6 |
| multiturn_coherence | 0 | 7 | 0% | 7 |
| prediction_sanity | 6 | 6 | 100% | 0 |
| scope_guardrail | 7 | 8 | 88% | 8 |

**Weakest category (by automated pass rate): multiturn_coherence (0%)**

Categories marked 'Needs Manual Review' > 0 require reading the response column and filling in manual_pass_fail before treating the automated rate as final � the automated check is a keyword/intent heuristic, not a real correctness judgment.

## Proposed improvement for the weakest category

(fill in after reviewing the actual failing cases � see reports/eval_results.csv)

## Benchmark comparison: match-winner model vs. naive ladder-position baseline

HistGradientBoosting model vs. a naive 'higher ladder position wins' baseline, walk-forward across the 3 most recent seasons (216 matches each)

| Season | Model Accuracy | Ladder Baseline Accuracy |
|---|---|---|
| 2023 | 74.1% | 65.3% |
| 2024 | 74.5% | 61.6% |
| 2025 | 66.7% | 67.1% |

Always-home baseline (2025, for reference): 55.6%

The model beats the ladder baseline in 2 of 3 seasons and is essentially tied in the third � not a blowout, but a real, consistent edge over a genuinely competitive baseline (ladder position itself beats the naive always-home baseline by ~10-12 points). This is the honest context for 'how good is good enough': a sports prediction model with irreducible outcome randomness should be judged against a strong simple baseline, not against 100% accuracy.