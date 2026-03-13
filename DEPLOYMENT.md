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

## Exposing The API
### Local Minikube
Minikube is not public by default. To expose staging on your machine with an ingress hostname:

```bash
minikube addons enable ingress
kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/staging
echo "$(minikube ip) visionflow-staging.local" | sudo tee -a /etc/hosts
curl -H "Host: visionflow-staging.local" http://$(minikube ip)/health
```

The staging ingress hostname is:
- `visionflow-staging.local`

### Real Public Access
For other people to use the platform without your laptop:
1. Push `visionflow-api` and `visionflow-worker` images to a registry.
2. Deploy the production overlay to a cloud Kubernetes cluster.
3. Install an ingress controller or use the cloud load balancer ingress.
4. Point a DNS record to the load balancer.
5. Create the TLS secret referenced by the production ingress.

The production ingress hostname placeholder is:
- `visionflow.example.com`

Update `/Users/ashimaverma/visionflow/k8s/overlays/prod/ingress.yaml` with your real domain before production deploy.

See the full public deployment steps in:
- `/Users/ashimaverma/visionflow/PUBLIC_DEPLOYMENT.md`

## CI/CD
- CI workflow: `.github/workflows/ci.yml`
- Runs tests, dependency scan, and container builds on push/PR.
