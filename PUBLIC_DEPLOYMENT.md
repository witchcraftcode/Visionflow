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
cd /Users/ashimaverma/visionflow
./scripts/publish_images.sh --registry ghcr.io/witchcraftcode --tag latest --push
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

Or render a fresh manifest from environment variables:
```bash
export VISIONFLOW_API_KEY=your-api-key
export VISIONFLOW_ADMIN_API_KEY=your-admin-key
python /Users/ashimaverma/visionflow/scripts/render_k8s_secret.py > /tmp/visionflow-secret.yaml
```

Create the secret in the cluster:
```bash
kubectl create namespace visionflow-prod
kubectl -n visionflow-prod apply -f /tmp/visionflow-secret.yaml
```

## 4. Prepare release manifests
Render the secret and ingress together and run preflight validation:
```bash
export VISIONFLOW_HOST=api.visionflow.yourdomain.com
./scripts/prepare_release.sh --overlay prod --output-dir /tmp/visionflow-release
```

## 5. Configure TLS
The rendered production ingress expects a TLS secret:
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
kubectl apply -f /tmp/visionflow-release/visionflow-secret.yaml
kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/prod
kubectl apply -f /tmp/visionflow-release/visionflow-ingress.yaml
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
