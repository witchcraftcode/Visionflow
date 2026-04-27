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
1. Build registry-ready images.
   ```bash
   ./scripts/publish_images.sh --registry ghcr.io/witchcraftcode --tag latest
   ```
2. Prepare release artifacts and validate them.
   ```bash
   export VISIONFLOW_API_KEY=your-api-key
   export VISIONFLOW_ADMIN_API_KEY=your-admin-key
   export VISIONFLOW_HOST=api.yourdomain.com
   ./scripts/prepare_release.sh --overlay prod --output-dir /tmp/visionflow-release
   ```
3. Create the TLS secret named `visionflow-tls`.
4. Deploy:
   ```bash
   kubectl apply -f /tmp/visionflow-release/visionflow-secret.yaml
   kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/prod
   kubectl apply -f /tmp/visionflow-release/visionflow-ingress.yaml
   ```
5. Point DNS to the ingress/load balancer.
6. Run a public smoke test against the deployed hostname:
   ```bash
   BASE_URL=https://your-real-domain VISIONFLOW_API_KEY=your-api-key ./scripts/smoke_test.sh
   ```

## EKS Production
1. Build ECR-ready images.
   ```bash
   export AWS_REGION=us-east-1
   export AWS_ACCOUNT_ID=676766460202
   ./scripts/publish_images.sh --registry ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com --tag latest --platform linux/amd64
   ```
2. Prepare EKS release artifacts and validate them.
   ```bash
   export VISIONFLOW_API_KEY=your-api-key
   export VISIONFLOW_ADMIN_API_KEY=your-admin-key
   export VISIONFLOW_HOST=api.yourdomain.com
   export VISIONFLOW_ACM_CERTIFICATE_ARN=arn:aws:acm:REGION:ACCOUNT:certificate/CERT_ID
   ./scripts/prepare_release.sh --overlay eks-prod --output-dir /tmp/visionflow-release
   ```
3. Apply:
   ```bash
   kubectl apply -f /tmp/visionflow-release/visionflow-secret.yaml
   kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/eks-prod
   kubectl apply -f /tmp/visionflow-release/visionflow-ingress.yaml
   ```

## EKS Temporary Public URL
1. Prepare a temporary public ALB release without a custom domain.
   ```bash
   export VISIONFLOW_API_KEY=your-api-key
   export VISIONFLOW_ADMIN_API_KEY=your-admin-key
   ./scripts/prepare_release.sh --overlay eks-prod --public-without-domain --output-dir /tmp/visionflow-release
   ```
2. Apply:
   ```bash
   kubectl apply -f /tmp/visionflow-release/visionflow-secret.yaml
   kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/eks-prod
   kubectl apply -f /tmp/visionflow-release/visionflow-ingress.yaml
   ```
3. Get the temporary ALB hostname:
   ```bash
   kubectl -n visionflow-prod get ingress visionflow-api
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
