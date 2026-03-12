# Runbook

## Local Bring-Up
```bash
cd /Users/ashimaverma/visionflow
docker compose up -d --build
docker compose ps
```

## Local Health Checks
```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/ready
```

## Common Incidents

### API unhealthy
1. Check container status: `docker compose ps`.
2. Check logs: `docker compose logs api --tail=200`.
3. Check Redis connectivity via `/ready`.

### Jobs stuck queued
1. Check worker status/logs.
2. Verify Redis queue depth (`/ready`).
3. Confirm model files exist in `app/models/onnx`.

### Frequent dead-letter jobs
1. Check worker logs for repeated `runtime_error`.
2. Validate model config and model artifact compatibility.
3. Reduce retry count or fix model/runtime mismatch.

## Kubernetes Bring-Up
```bash
kubectl apply -f /Users/ashimaverma/visionflow/k8s
kubectl get pods
kubectl port-forward svc/visionflow-api 8000:8000
```

## Rollback
```bash
kubectl rollout undo deployment/visionflow-api
kubectl rollout undo deployment/visionflow-worker
```
