# VisionFlow

VisionFlow is a simple ML model deployment service: upload an image, pick a model, and get a prediction. The API enqueues jobs in Redis and a worker performs inference.

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

4. Poll job status:

```bash
JOB_ID=$(curl -s -X POST -F model=resnet18 -F file=@/Users/ashimaverma/visionflow/test.jpg http://localhost:8000/predict | jq -r .job_id)

curl -s http://localhost:8000/status/$JOB_ID | jq
```

5. Run the live smoke test:

```bash
./scripts/smoke_test.sh
```

6. Verify bundled ONNX artifacts load and produce predictions:

```bash
source /Users/ashimaverma/visionflow/.venv/bin/activate
python /Users/ashimaverma/visionflow/scripts/verify_models.py
```

## Kubernetes
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

## Config
Per-model preprocessing configs live in:
- /Users/ashimaverma/visionflow/app/configs/models/resnet18.json
- /Users/ashimaverma/visionflow/app/configs/models/mobilenet.json
- /Users/ashimaverma/visionflow/app/configs/models/yolov5.json

Adjust `input_size`, `color_mode`, and `normalization` to match each model.

## API
- `GET /models`
- `GET /models/{model_name}/versions`
- `POST /models/register`
- `POST /models/{model_name}/promote`
- `GET /admin/audit`
- `POST /predict` (multipart form: `model`, `file`)
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
- `JOB_TTL_SECONDS` (default `86400`)
- `IDEMPOTENCY_TTL_SECONDS` (default `3600`)
- `VISIONFLOW_API_KEY` (optional; if set, API requires `X-API-Key`)
- `VISIONFLOW_ADMIN_API_KEY` (optional; if set, admin endpoints require `X-Admin-Key`)
- `RATE_LIMIT_REQUESTS` (default `60`)
- `RATE_LIMIT_WINDOW_SECONDS` (default `60`)
- `AUDIT_LOG_LIMIT` (default `200`)

## Quick Git Sync
Use helper script to commit and push local changes:

```bash
/Users/ashimaverma/visionflow/scripts/sync_to_github.sh "your commit message"
```
