# Public Deployment

This is the minimum path to make VisionFlow reachable by other people over the internet.

## 1. Publish container images
The production overlay expects these images:
- `ghcr.io/witchcraftcode/visionflow-api:latest`
- `ghcr.io/witchcraftcode/visionflow-worker:latest`

You can publish them from GitHub Actions using the workflow in:
- `/Users/ashimaverma/visionflow/.github/workflows/publish-images.yml`

Or locally:
```bash
docker build -t ghcr.io/witchcraftcode/visionflow-api:latest -f /Users/ashimaverma/visionflow/Dockerfile.api /Users/ashimaverma/visionflow
docker build -t ghcr.io/witchcraftcode/visionflow-worker:latest -f /Users/ashimaverma/visionflow/Dockerfile.worker /Users/ashimaverma/visionflow
docker push ghcr.io/witchcraftcode/visionflow-api:latest
docker push ghcr.io/witchcraftcode/visionflow-worker:latest
```

If you use a different registry, update:
- `/Users/ashimaverma/visionflow/k8s/overlays/prod/kustomization.yaml`

## 2. Create a real Kubernetes cluster
Use any managed Kubernetes provider:
- GKE
- EKS
- AKS
- DigitalOcean Kubernetes

You need:
- a working `kubectl` context
- an ingress controller or cloud load balancer ingress
- a public DNS name

## 3. Create production secrets
Do not commit real secrets into git.

Use the example file:
- `/Users/ashimaverma/visionflow/k8s/overlays/prod/secret.example.yaml`

Create the secret in the cluster:
```bash
kubectl create namespace visionflow-prod
kubectl -n visionflow-prod apply -f /Users/ashimaverma/visionflow/k8s/overlays/prod/secret.example.yaml
```

Then replace the placeholder values:
```bash
kubectl -n visionflow-prod edit secret visionflow-secrets
```

## 4. Configure the domain
Update the hostname in:
- `/Users/ashimaverma/visionflow/k8s/overlays/prod/ingress.yaml`

Replace:
- `visionflow.example.com`

With your real domain, for example:
- `api.visionflow.yourdomain.com`

## 5. Configure TLS
The production ingress expects a TLS secret:
- `visionflow-tls`

Create it with your certificate:
```bash
kubectl -n visionflow-prod create secret tls visionflow-tls \
  --cert=/path/to/tls.crt \
  --key=/path/to/tls.key
```

If you use cert-manager instead, update the ingress annotations and let cert-manager manage the secret.

## 6. Deploy production
```bash
kubectl apply -f /Users/ashimaverma/visionflow/k8s/namespaces.yaml
kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/prod
```

## 7. Point DNS to the load balancer
After the ingress/load balancer is created, point your domain to the external address:
```bash
kubectl -n visionflow-prod get ingress
```

## 8. Verify
```bash
curl https://your-real-domain/health
curl https://your-real-domain/ready
curl -H "X-API-Key: your-api-key" https://your-real-domain/models
```

## Notes
- Minikube is only for development/staging validation on your laptop.
- Real public access requires a real cloud endpoint, not `localhost` or Minikube IP.
- If your registry is private, add an `imagePullSecret` to the production namespace and reference it in the deployments.
