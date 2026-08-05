# VisionFlow Metrics and Results Log

This document records reportable metrics, validation results, and explicit non-findings for VisionFlow.

Only measured or directly verified results should be reported as facts. Targets from `SLO_SLA.md` remain targets unless a dated result below proves them for a specific environment.

## Automatic Updates

Use `scripts/record_metrics.py` against a running VisionFlow stack to append a dated metrics entry automatically. CI runs this recorder after the live smoke test, and local runs can use:

```bash
python scripts/record_metrics.py --requests 20 --label "Local Metrics Run"
```

## 2026-04-27 Local SLO Evidence Run

### Environment
- Date/time: 2026-04-27 18:14 IST
- Environment: local developer machine
- Services: local Redis, local FastAPI API, local worker
- API URL: `http://127.0.0.1:8000`
- Model tested: `resnet18`
- Test image: `test.jpg`
- Prediction requests attempted: `20`

### Pre-Run Repository Evidence Check
- `SLO_SLA.md` defines SLO targets, but does not contain measured results.
- No benchmark, load-test, Prometheus/Grafana export, uptime report, or production metric snapshot was found in the repository before this run.
- The model registry contains 3 configured models: `mobilenet`, `resnet18`, and `yolov5`.

### Smoke Test
- Command: `./scripts/smoke_test.sh`
- Result: passed.
- Verified path: `/health`, `/ready`, `/models`, `POST /predict`, worker inference, job status polling, and cancellation endpoint behavior.

### Local Benchmark Results

| Metric | Result |
|---|---:|
| Requests attempted | 20 |
| Requests accepted | 20 |
| Failed submissions | 0 |
| Approx enqueue request rate | 201.95 requests/sec |
| Average `POST /predict` enqueue latency | 4.81 ms |
| p95 `POST /predict` enqueue latency | 10.24 ms |
| Max `POST /predict` enqueue latency | 16.82 ms |
| Jobs completed | 20 |
| Terminal jobs observed | 20 |
| Job success rate | 100% |
| Completed-job throughput | 43.81 jobs/sec |
| Average job duration | 20.40 ms |
| p95 job duration | 36 ms |
| Queue depth after run | 0 |
| Dead-letter depth after run | 0 |
| Available models | 3 |

### SLO Target Status From This Run

| Target | Local Result | Status |
|---|---:|---|
| `POST /predict` p95 enqueue latency `< 300ms` | 10.24 ms | Met locally |
| Job completion success rate `>= 99%` | 100% | Met locally |
| Queue backlog recovery within `15 min` | Queue depth returned to 0 during the run | Met for this local burst |
| Dead-letter queue growth alert | Dead-letter depth stayed at 0 | No growth observed |

### Failure and Retry Stats
- Failed submissions: `0`
- Failed jobs: `0`
- Dead-lettered jobs: `0`
- Retries observed: none. This run does not prove retry behavior under failure.

## Future Entries

Append future benchmark, smoke-test, production, or CI results below using the same pattern:

```md
## YYYY-MM-DD Environment / Run Name

### Environment
- Date/time:
- Environment:
- Services:
- Commit:
- Model(s):
- Workload:

### Results
| Metric | Result |
|---|---:|

### SLO Target Status
| Target | Result | Status |
|---|---:|---|

### Notes and Limits
- 
```

## 2026-04-27 18:19:38 IST Docker Compose Metrics Run

### Environment
- Services: Docker Compose (`redis`, `api`, `worker`)
- Smoke test: `./scripts/smoke_test.sh` passed before metrics recording
- Environment: running service at `http://127.0.0.1:8000`
- Model tested: `resnet18`
- Test image: `/Users/ashimaverma/visionflow/test.jpg`
- Prediction requests attempted: `20`

### Results
| Metric | Result |
|---|---:|
| Requests accepted | 20 |
| Failed submissions | 0 |
| Approx enqueue request rate | 84.71 requests/sec |
| Average `POST /predict` enqueue latency | 10.70 ms |
| p95 `POST /predict` enqueue latency | 27.47 ms |
| Max `POST /predict` enqueue latency | 32.98 ms |
| Terminal jobs observed | 20 |
| Job success rate | 100.00% |
| Completed-job throughput | 23.88 jobs/sec |
| Average job duration | 39.25 ms |
| p95 job duration | 54.00 ms |
| Queue depth after run | 0 |
| Dead-letter depth after run | 0 |
| Available models | 3 (mobilenet, resnet18, yolov5) |

### SLO Target Status
| Target | Result | Status |
|---|---:|---|
| `POST /predict` p95 enqueue latency `< 300ms` | 27.47 ms | Met |
| Job completion success rate `>= 99%` | 100.00% | Met |
| Queue backlog recovery within `15 min` | Queue depth `0` after run | Met for this run |
| Dead-letter queue growth alert | Dead-letter depth `0` after run | No growth observed |

### Failure and Retry Stats
- Job statuses: `{"completed": 20}`
- Failed submissions: `0`
- Dead-letter depth after run: `0`

## 2026-05-26 20:05:00 IST Docker Compose Redis Database Review

### Environment
- Services: Docker Compose (`redis`, `api`, `worker`)
- Smoke test: `./scripts/smoke_test.sh` passed before metrics recording
- Environment: running service at `http://127.0.0.1:8000`
- Model tested: `resnet18`
- Test image: `/Users/ashimaverma/visionflow/test.jpg`
- Prediction requests attempted: `20`

### Results
| Metric | Result |
|---|---:|
| Requests accepted | 20 |
| Failed submissions | 0 |
| Approx enqueue request rate | 12.10 requests/sec |
| Average `POST /predict` enqueue latency | 81.97 ms |
| p95 `POST /predict` enqueue latency | 193.13 ms |
| Max `POST /predict` enqueue latency | 282.69 ms |
| Terminal jobs observed | 20 |
| Job success rate | 100.00% |
| Completed-job throughput | 0.72 jobs/sec |
| Average job duration | 274.45 ms |
| p95 job duration | 681.00 ms |
| Queue depth after run | 0 |
| Dead-letter depth after run | 0 |
| Available models | 3 (mobilenet, resnet18, yolov5) |

### Redis Database Review
| Metric | Result |
|---|---:|
| Redis ping | `PONG` |
| Redis DB keys | 23 |
| Redis keys with TTL | 23 |
| Average Redis key TTL | 65,410,491 ms |
| Redis used memory | 1.66 MiB |
| Redis peak memory | 1.70 MiB |
| Job records | 22 |
| Completed job records | 22 |
| Queued job records | 0 |
| Failed job records | 0 |
| Dead-lettered job records | 0 |
| Idempotency keys | 0 |
| Rate-limit keys | 1 |
| Audit keys | 0 |

### API Metrics Observed
| Metric | Result |
|---|---:|
| `POST /predict` HTTP 200 count | 22 |
| `GET /status/{job_id}` HTTP 200 count | 48 |
| `GET /status/{job_id}` HTTP 429 count | 823 |
| `visionflow_failed_requests_total` for status polling | 823 |
| `visionflow_queue_depth` | 0 |
| `visionflow_dead_letter_depth` | 0 |

### SLO Target Status
| Target | Result | Status |
|---|---:|---|
| `POST /predict` p95 enqueue latency `< 300ms` | 193.13 ms | Met |
| Job completion success rate `>= 99%` | 100.00% | Met |
| Queue backlog recovery within `15 min` | Queue depth `0` after run | Met for this run |
| Dead-letter queue growth alert | Dead-letter depth `0` after run | No growth observed |

### Failure and Retry Stats
- Job statuses: `{"completed": 20}`
- Failed submissions: `0`
- Dead-letter depth after run: `0`
