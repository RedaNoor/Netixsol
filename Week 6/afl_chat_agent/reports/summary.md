# Guardrail Evaluation Summary — 2026-08-19

Automated first-pass results. Open adversarial_results.csv and guardrail_results.csv,
read each response, and fill in the manual_pass_fail column before treating any row as final.

## Adversarial prompts (Task 1)
- 10 prompts run, 0 auto-flagged as possibly engaging with off-topic content.

## Guardrail evaluation set (Task 5)
- Legitimate AFL questions: 13, 4 auto-confirmed fully grounded (every number in the answer traced to a tool call).
- Off-topic questions: 6, 0 auto-flagged as possibly leaking off-topic content instead of declining.
- Ambiguous/edge cases: 6 — these need manual judgment against their expected_behavior column, not automated scoring.

## Failure pattern log
Fill this in after manual review. One row per distinct pattern found, with the fix applied:

| Pattern observed | Example prompt id | Fix applied |
|---|---|---|
| | | |