# Production Monitoring Checklist

## Reliability
- Track HTTP 4xx/5xx, graph failures, model failures and tool failures.
- Alert when 5xx > 2% over 15 minutes or model/tool failures > 5% over 15 minutes.

## Latency
- Track p50/p95/p99 end-to-end latency and model latency separately.
- Alert when p95 > 8 seconds for 15 minutes or >2x the 7-day baseline.

## Cost
- Track provider-reported prompt/completion tokens and estimated cost per run.
- Alert when cost per successful run >1.5x the rolling 7-day baseline.

## Quality
- Track task success, feasibility correctness, commercial consistency, safety and reviewer rejection/edit rate.
- Alert when offline evaluation average <4/5 or task success <90%.

## Human oversight
- Track approval rate, rejection rate, approval time and reviewer rejection reasons.
- Investigate sustained rejection >25% for a week.

## Safety
- Track prompt-injection rejections, unsafe guarantee phrases and approval-bypass attempts.
- Treat approval-bypass as a critical incident.

## Re-evaluation
- Run smoke evaluation after every prompt/model/workflow change.
- Run a broader regression weekly during active development and monthly after stabilization.
