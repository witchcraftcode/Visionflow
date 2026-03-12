# SLO / SLA Draft

## Service Level Objectives (SLO)
- API availability: `99.5%` monthly.
- `POST /predict` p95 latency (enqueue only): `< 300ms`.
- Job completion success rate: `>= 99%` (excluding user input errors).
- Queue backlog recovery: backlog drains to steady state within `15 min` after burst.

## Error Budget
- Monthly downtime budget at 99.5%: `~3h 39m`.

## Alert Triggers (Initial)
- API 5xx rate > 2% for 5 min.
- Queue depth above threshold for 10 min.
- Dead-letter queue growth over threshold.
- Worker restart loops.

## SLA (External, Future)
- To be defined once auth, tenancy, and billing are in place.
