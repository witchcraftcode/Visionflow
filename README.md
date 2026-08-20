# VisionFlow

VisionFlow is a simple ML model deployment service: upload an image, pick a model, and get a prediction. The API enqueues jobs in Redis and a worker performs inference.

It is structured like a production-minded ML inference platform: queue-backed workers, retries and dead-letter handling, Prometheus/Grafana observability, benchmark scripts, Kubernetes overlays, and automated CI validation.

## Project Structure

```text
app/
  main.py                    FastAPI app assembly
  api/v1/                    Versioned route modules
  core/                      Config, request middleware, and structured logging
  db/                        SQLAlchemy engine, sessions, and ORM models
  services/                  Queue, registry, and inference service boundaries
  worker/                    Background job processor for model inference
  worker_runner.py           Worker process entry point
  queue/redis_queue.py       Redis queue, job store, idempotency, and rate-limit helpers
  models/                    Model loaders, ONNX wrappers, and prediction adapters
  models/onnx/               Bundled ONNX model artifacts
  preprocessing/image.py     Image decoding, resizing, color conversion, and normalization
  configs/model_registry.json
                             Seed data for the PostgreSQL-backed model registry
  configs/models/*.json      Per-model preprocessing settings
  security.py                API key, admin key, and rate-limit checks
  observability.py           Structured logs and Prometheus-style metrics
  monitoring/drift.py        Simple feature and prediction drift monitor
  audit.py                   Redis-backed admin audit events

scripts/                     Bootstrap, smoke test, metrics, release, and deploy helpers
observability/               Prometheus and Grafana provisioning plus dashboard definitions
docs/                        Architecture diagrams and system design notes
tests/                       Unit and integration-style test coverage
k8s/base/                    Shared Kubernetes resources managed by Kustomize
k8s/overlays/                Environment-specific staging, prod, and EKS overlays
.github/workflows/           CI and image publishing workflows
```

## Requirements
- Docker and Docker Compose
- Python 3.12 recommended for local development
- ONNX model files placed at:
  - /Users/ashimaverma/visionflow/app/models/onnx/resnet18.onnx
  - /Users/ashimaverma/visionflow/app/models/onnx/mobilenet_v2.onnx
  - /Users/ashimaverma/visionflow/app/models/onnx/yolov5n.onnx

## Local Python Bootstrap
Prepare a consistent local environment with:

```bash
cd /Users/ashimaverma/visionflow
./scripts/bootstrap.sh
source /Users/ashimaverma/visionflow/.venv/bin/activate
python -m pytest -q
```

## Local (Docker Compose)
1. Build and start services:

```bash
cd /Users/ashimaverma/visionflow
docker compose up --build
```

2. Check available models:

```bash
curl -s http://localhost:8000/models | jq
```

3. Send a prediction request:

```bash
curl -s -X POST \
  -F model=resnet18 \
  -F file=@/Users/ashimaverma/visionflow/test.jpg \
  http://localhost:8000/predict | jq
```

4. Send a prediction request for a specific model version:

```bash
curl -s -X POST \
  -F model=resnet18 \
  -F model_version=1.0.0 \
  -F file=@/Users/ashimaverma/visionflow/test.jpg \
  http://localhost:8000/predict | jq
```

5. Reuse a prediction request with an idempotency key:

```bash
curl -s -X POST \
  -H "Idempotency-Key: demo-request-1" \
  -F model=resnet18 \
  -F file=@/Users/ashimaverma/visionflow/test.jpg \
  http://localhost:8000/predict | jq
```

6. Poll job status:

```bash
JOB_ID=$(curl -s -X POST -F model=resnet18 -F file=@/Users/ashimaverma/visionflow/test.jpg http://localhost:8000/predict | jq -r .job_id)

curl -s http://localhost:8000/status/$JOB_ID | jq
```

7. Run the live smoke test:

```bash
./scripts/smoke_test.sh
```

8. Record live metrics and append them to `/Users/ashimaverma/visionflow/METRICS_RESULTS.md`:

```bash
python /Users/ashimaverma/visionflow/scripts/record_metrics.py --requests 20 --label "Local Metrics Run"
```

9. Start Prometheus + Grafana for the observability dashboard:

```bash
docker compose --profile observability up -d
```

Then open:
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

10. Install optional benchmark extras for native YOLO and GPU telemetry:

```bash
python -m pip install -r /Users/ashimaverma/visionflow/requirements-benchmarks.txt
```

11. Run the benchmark suite and generate `/Users/ashimaverma/visionflow/BENCHMARK_RESULTS.md`:

```bash
python /Users/ashimaverma/visionflow/scripts/run_benchmarks.py --base-url http://127.0.0.1:8000
```

The benchmark suite now covers:
- concurrent users
- p95/p99 latency
- scaling behavior across concurrency levels
- HTTP batch-size comparisons
- ONNX vs native runtime comparisons for YOLO when optional dependencies are installed
- CPU vs GPU runtime comparisons when CUDA providers are available

12. Review the architecture diagrams:

```bash
open /Users/ashimaverma/visionflow/docs/ARCHITECTURE.md
```

13. Verify bundled ONNX artifacts load and produce predictions:

```bash
source /Users/ashimaverma/visionflow/.venv/bin/activate
python /Users/ashimaverma/visionflow/scripts/verify_models.py
```

14. Render a real Kubernetes secret manifest from environment variables:

```bash
export VISIONFLOW_API_KEY=your-api-key
export VISIONFLOW_ADMIN_API_KEY=your-admin-key
python /Users/ashimaverma/visionflow/scripts/render_k8s_secret.py > /tmp/visionflow-secret.yaml
```

15. Run a production preflight check before deploy:

```bash
python /Users/ashimaverma/visionflow/scripts/validate_deployment.py --overlay prod
```

16. Render a real ingress manifest without editing tracked YAML:

```bash
export VISIONFLOW_HOST=api.yourdomain.com
python /Users/ashimaverma/visionflow/scripts/render_ingress.py --overlay prod > /tmp/visionflow-ingress.yaml
```

CI now renders and validates deploy-time secret and ingress manifests for both `prod` and `eks-prod`, so placeholder deployment inputs fail before image publish or release steps. CI also runs `scripts/record_metrics.py` after the live smoke test so each validation flow produces a metrics-log entry.

17. Prepare a production release bundle and print the exact `kubectl` commands:

```bash
export VISIONFLOW_API_KEY=your-api-key
export VISIONFLOW_ADMIN_API_KEY=your-admin-key
export VISIONFLOW_HOST=api.yourdomain.com
./scripts/prepare_release.sh --overlay prod
```

18. Build registry-ready images before the infra handoff:

```bash
./scripts/publish_images.sh --registry ghcr.io/witchcraftcode --tag latest
```

## Kubernetes
Kubernetes resources are organized around Kustomize:

- `/Users/ashimaverma/visionflow/k8s/base` contains the shared API, worker, Redis, service, HPA, PDB, config map, and network-policy resources.
- `/Users/ashimaverma/visionflow/k8s/overlays/staging` is the local/staging overlay.
- `/Users/ashimaverma/visionflow/k8s/overlays/prod` is the standard production overlay.
- `/Users/ashimaverma/visionflow/k8s/overlays/eks-prod` is the EKS production overlay.

The root-level files in `/Users/ashimaverma/visionflow/k8s` are retained for compatibility with earlier deployment flows. Prefer the `base` plus `overlays` layout for new deployments.

1. Build images locally (or push to a registry and update image names):

```bash
docker build -t visionflow-api -f /Users/ashimaverma/visionflow/Dockerfile.api /Users/ashimaverma/visionflow
docker build -t visionflow-worker -f /Users/ashimaverma/visionflow/Dockerfile.worker /Users/ashimaverma/visionflow
```

2. For Minikube, load the images:

```bash
minikube image load visionflow-api
minikube image load visionflow-worker
```

3. Apply manifests:

```bash
kubectl apply -f /Users/ashimaverma/visionflow/k8s/namespaces.yaml
kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/staging
```

4. Expose staging through Minikube ingress:

```bash
minikube addons enable ingress
echo "$(minikube ip) visionflow-staging.local" | sudo tee -a /etc/hosts
curl -H "Host: visionflow-staging.local" http://$(minikube ip)/health
```

5. Use the same curl commands as above against `http://$(minikube ip)` and pass the ingress host:

```bash
curl -s -H "Host: visionflow-staging.local" http://$(minikube ip)/models | jq
```

For real public access, deploy the production overlay to a cloud Kubernetes cluster, push your images to a registry, and point a real DNS name at the ingress/load balancer. The production ingress template lives at `/Users/ashimaverma/visionflow/k8s/overlays/prod/ingress.yaml`.

A complete public deployment guide is in:
- `/Users/ashimaverma/visionflow/PUBLIC_DEPLOYMENT.md`
- `/Users/ashimaverma/visionflow/EKS_DEPLOYMENT.md`

## Observability
- Prometheus scrapes `/metrics` from the API and can be started locally from `/Users/ashimaverma/visionflow/observability/prometheus/prometheus.yml`.
- Grafana provisioning and the `VisionFlow Overview` dashboard are under `/Users/ashimaverma/visionflow/observability/grafana`.
- Dashboard panels cover throughput, latency, queue depth, dead-letter depth, failed requests, worker CPU/memory/GPU utilization, and model-wise inference latency.

## Benchmarking
- `scripts/run_benchmarks.py` produces concurrency, batch-size, and runtime-comparison benchmark reports.
- `BENCHMARK_RESULTS.md` is the canonical benchmark artifact for the repo.
- The benchmark suite measures concurrent-user load, throughput, p95/p99 latency, HTTP batch behavior, and model/runtime comparisons.
- Optional extras in `/Users/ashimaverma/visionflow/requirements-benchmarks.txt` enable native YOLO and GPU telemetry benchmarking.

## Fault Tolerance
- Retries with exponential backoff are implemented in the worker.
- Dead-letter queue handling is implemented in Redis.
- Timeout handling is enforced per job.
- Stale in-flight jobs are automatically recovered and requeued or dead-lettered after worker interruption.
- Cancellation requests degrade gracefully and are honored before inference runs.

## Cloud Deployment
- AWS and EKS deployment paths are documented in `/Users/ashimaverma/visionflow/PUBLIC_DEPLOYMENT.md` and `/Users/ashimaverma/visionflow/EKS_DEPLOYMENT.md`.
- A low-cost managed deployment option is provided in `/Users/ashimaverma/visionflow/render.yaml`.

## Config
Per-model preprocessing configs live in:
- /Users/ashimaverma/visionflow/app/configs/models/resnet18.json
- /Users/ashimaverma/visionflow/app/configs/models/mobilenet.json
- /Users/ashimaverma/visionflow/app/configs/models/yolov5.json

Adjust `input_size`, `color_mode`, and `normalization` to match each model.

Model registry metadata is stored in SQL tables (`models`, `model_versions`, `jobs`, `deployments`).
For local development, `DATABASE_URL` defaults to `sqlite:///./visionflow.db`; for RDS, set it to a PostgreSQL URL and run:

```bash
alembic upgrade head
```

## API
- `GET /models`
- `GET /models/{model_name}/versions`
- `GET /models/{model_name}/versions/{version}`
- `POST /models/register`
- `PUT /models/{model_name}/versions/{version}`
- `DELETE /models/{model_name}/versions/{version}`
- `POST /models/{model_name}/promote`
- `GET /admin/audit`
- `POST /predict` (multipart form: `model`, optional `model_version`, `file`; optional `Idempotency-Key` header)
- `POST /predict/batch` (multipart form: `model`, optional `model_version`, `files`; optional `Idempotency-Key` header)
- `GET /status/{job_id}`
- `POST /jobs/{job_id}/cancel`
- `GET /health`
- `GET /ready`
- `GET /metrics`
- `POST /monitoring/drift/baseline`
- `POST /monitoring/drift/observe`
- `GET /monitoring/drift/summary`

## Environment Variables
- `MAX_UPLOAD_BYTES` (default `5242880`)
- `DEFAULT_JOB_TIMEOUT_SECONDS` (default `60`)
- `REDIS_HOST` (default `localhost`)
- `REDIS_PORT` (default `6379`)
- `JOB_TTL_SECONDS` (default `86400`)
- `IDEMPOTENCY_TTL_SECONDS` (default `3600`)
- `VISIONFLOW_API_KEY` (optional; if set, API requires `X-API-Key`)
- `VISIONFLOW_ADMIN_API_KEY` (optional; if set, admin endpoints require `X-Admin-Key`)
- `RATE_LIMIT_REQUESTS` (default `60`)
- `RATE_LIMIT_WINDOW_SECONDS` (default `60`)
- `AUDIT_LOG_LIMIT` (default `200`)
- `DATABASE_URL` (default `sqlite:///./visionflow.db`; use PostgreSQL/RDS in deployed environments)
- `AUTO_CREATE_SQLITE_SCHEMA` (default `true`; local SQLite convenience only)

## Quick Git Sync
Use helper script to commit and push local changes:

```bash
/Users/ashimaverma/visionflow/scripts/sync_to_github.sh "your commit message"
```
