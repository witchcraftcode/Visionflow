# Deployment

## Environments
- `visionflow-dev`
- `visionflow-staging`
- `visionflow-prod`

Create namespaces:
```bash
kubectl apply -f /Users/ashimaverma/visionflow/k8s/namespaces.yaml
```

## Apply Core Manifests
```bash
kubectl apply -f /Users/ashimaverma/visionflow/k8s/configmap.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/secret.example.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/redis-deployment.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/redis-service.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/api-deployment.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/api-service.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/worker-deployment.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/hpa-api.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/hpa-worker.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/pdb-api.yaml
kubectl apply -f /Users/ashimaverma/visionflow/k8s/network-policy.yaml
```

## Kustomize Overlays
- Staging:
```bash
kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/staging
```
- Production:
```bash
kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/prod
```

## CI/CD
- CI workflow: `.github/workflows/ci.yml`
- Runs tests, dependency scan, and container builds on push/PR.
