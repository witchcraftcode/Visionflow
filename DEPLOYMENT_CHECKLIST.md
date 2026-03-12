# Deployment Checklist

## Local
1. Start Docker Desktop.
2. Run:
   ```bash
   cd /Users/ashimaverma/visionflow
   docker compose up -d --build
   ```
3. Verify:
   ```bash
   curl -s http://localhost:8000/health
   curl -s http://localhost:8000/ready
   curl -s -H "X-API-Key: ${VISIONFLOW_API_KEY:-}" http://localhost:8000/models
   ```
4. Run one prediction:
   ```bash
   curl -s -X POST \
     -H "X-API-Key: ${VISIONFLOW_API_KEY:-}" \
     -F model=resnet18 \
     -F file=@/Users/ashimaverma/visionflow/test.jpg \
     http://localhost:8000/predict
   ```

## Staging Kubernetes
1. Ensure cluster is running and current context is correct.
2. Create namespaces:
   ```bash
   kubectl apply -f /Users/ashimaverma/visionflow/k8s/namespaces.yaml
   ```
3. Deploy staging overlay:
   ```bash
   kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/staging
   ```
4. Verify:
   ```bash
   kubectl -n visionflow-staging get pods
   kubectl -n visionflow-staging get svc
   kubectl -n visionflow-staging port-forward svc/visionflow-api 8000:8000
   ```
5. Re-run local API checks against the forwarded port.

## GitHub
1. Commit:
   ```bash
   git -C /Users/ashimaverma/visionflow add -A
   git -C /Users/ashimaverma/visionflow commit -m "Finalize minimal workable platform"
   ```
2. Push:
   ```bash
   git -C /Users/ashimaverma/visionflow push
   ```
