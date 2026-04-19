# EKS Deployment

This is the minimum path to expose VisionFlow publicly on AWS EKS.

## What this uses
1. Amazon ECR for container images
2. Amazon EKS for Kubernetes
3. AWS Load Balancer Controller for a public ALB
4. Route 53 or any DNS provider for your API domain
5. AWS Certificate Manager for TLS

## 1. Prerequisites
Install and configure:
- `aws`
- `kubectl`
- `eksctl`
- `helm`

Authenticate AWS:
```bash
aws configure
aws sts get-caller-identity
```

Set variables:
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=676766460202
export CLUSTER_NAME=visionflow-prod
```

## 2. Create ECR repositories
```bash
aws ecr create-repository --repository-name visionflow-api --region $AWS_REGION
aws ecr create-repository --repository-name visionflow-worker --region $AWS_REGION
```

Log in to ECR:
```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

## 3. Build and push images
```bash
docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/visionflow-api:latest -f /Users/ashimaverma/visionflow/Dockerfile.api /Users/ashimaverma/visionflow
docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/visionflow-worker:latest -f /Users/ashimaverma/visionflow/Dockerfile.worker /Users/ashimaverma/visionflow

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/visionflow-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/visionflow-worker:latest
```

## 4. Create the EKS cluster
Use:
- `/Users/ashimaverma/visionflow/eksctl-cluster.yaml`

Create it:
```bash
eksctl create cluster -f /Users/ashimaverma/visionflow/eksctl-cluster.yaml
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
```

## 5. Install AWS Load Balancer Controller
Create the IAM policy first:
```bash
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.14.1/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json
```

Then create the IAM service account:
```bash
eksctl create iamserviceaccount \
  --cluster $CLUSTER_NAME \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```

Install the controller with Helm:
```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=$AWS_REGION \
  --set vpcId=$(aws eks describe-cluster --name $CLUSTER_NAME --region $AWS_REGION --query "cluster.resourcesVpcConfig.vpcId" --output text)
```

## 6. Create VisionFlow secrets
Create the namespace and secret:
```bash
kubectl apply -f /Users/ashimaverma/visionflow/k8s/namespaces.yaml
kubectl -n visionflow-prod apply -f /Users/ashimaverma/visionflow/k8s/overlays/eks-prod/secret.example.yaml
kubectl -n visionflow-prod edit secret visionflow-secrets
```

## 7. Configure TLS and domain
1. Request or import a certificate in AWS Certificate Manager.
2. Set your real hostname in:
   - `/Users/ashimaverma/visionflow/k8s/overlays/eks-prod/ingress.yaml`
3. Add this annotation to the ingress with your ACM certificate ARN:

```yaml
alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:REGION:ACCOUNT:certificate/CERT_ID
```

4. Point your DNS record to the ALB hostname after deployment.

## 8. Set ECR image names in the overlay
Update:
- `/Users/ashimaverma/visionflow/k8s/overlays/eks-prod/kustomization.yaml`

Replace:
- `REGION`

With your real AWS region. The account ID is already set to `676766460202`.

## 9. Deploy VisionFlow to EKS
```bash
kubectl apply -k /Users/ashimaverma/visionflow/k8s/overlays/eks-prod
```

Check rollout:
```bash
kubectl -n visionflow-prod get pods
kubectl -n visionflow-prod get ingress
```

## 10. Verify
Once the ALB is created and DNS is pointing correctly:
```bash
curl https://api.visionflow.example.com/health
curl https://api.visionflow.example.com/ready
curl -H "X-API-Key: your-api-key" https://api.visionflow.example.com/models
```

## Notes
1. The current overlay assumes public ALB access.
2. Redis is still in-cluster. For stronger production durability, move Redis to Amazon ElastiCache later.
3. The current worker is CPU-based and ONNX-focused.
