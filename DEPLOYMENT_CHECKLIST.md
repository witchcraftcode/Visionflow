# Deployment Checklist

## Local
1. Prepare the Python environment:
   ```bash
   cd /Users/ashimaverma/visionflow
   ./scripts/bootstrap.sh
   source /Users/ashimaverma/visionflow/.venv/bin/activate
   python -m pytest -q
   python /Users/ashimaverma/visionflow/scripts/verify_models.py
   ```
2. Start Docker Desktop.
3. Run:
   ```bash
   cd /Users/ashimaverma/visionflow
   docker compose up -d --build
   ```
4. Verify:
   ```bash
   curl -s http://localhost:8000/health
   curl -s http://localhost:8000/ready
   curl -s -H "X-API-Key: ${VISIONFLOW_API_KEY:-}" http://localhost:8000/models
   ```
5. Run one prediction:
   ```bash
   curl -s -X POST \
     -H "X-API-Key: ${VISIONFLOW_API_KEY:-}" \
     -F model=resnet18 \
     -F file=@/Users/ashimaverma/visionflow/test.jpg \
     http://localhost:8000/predict
   ```
6. Run the end-to-end smoke test:
   ```bash
   ./scripts/smoke_test.sh
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
   kubectl -n visionflow-staging get ingress
   ```
5. Enable ingress and map hostname locally:
   ```bash
   minikube addons enable ingress
   echo "$(minikube ip) visionflow-staging.local" | sudo tee -a /etc/hosts
   ```
6. Verify:
   ```bash
   curl -s -H "Host: visionflow-staging.local" http://$(minikube ip)/health
   curl -s -H "Host: visionflow-staging.local" http://$(minikube ip)/ready
   ```

## Public Production
1. Push `visionflow-api` and `visionflow-worker` to a registry.
2. Create production secrets for `VISIONFLOW_API_KEY` and `VISIONFLOW_ADMIN_API_KEY`.
3. Update `/Users/ashimaverma/visionflow/k8s/overlays/prod/ingress.yaml` with your real domain.
4. Create the TLS secret named `visionflow-tls`.
5. Deploy:
   ```bash
   kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/prod
   ```
6. Point DNS to the ingress/load balancer.
7. Run a public smoke test against the deployed hostname:
   ```bash
   BASE_URL=https://your-real-domain VISIONFLOW_API_KEY=your-api-key ./scripts/smoke_test.sh
   ```

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
