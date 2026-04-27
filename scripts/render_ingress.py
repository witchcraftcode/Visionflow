import argparse
import os
import sys


def render_prod_ingress(host: str, tls_secret_name: str) -> str:
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: visionflow-api
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "25m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - {host}
      secretName: {tls_secret_name}
  rules:
    - host: {host}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: visionflow-api
                port:
                  number: 8000
"""


def render_eks_ingress(host: str, certificate_arn: str) -> str:
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: visionflow-api
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/listen-ports: '[{{"HTTP": 80}}, {{"HTTPS": 443}}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/backend-protocol: HTTP
    alb.ingress.kubernetes.io/certificate-arn: {certificate_arn}
spec:
  ingressClassName: alb
  tls:
    - hosts:
        - {host}
  rules:
    - host: {host}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: visionflow-api
                port:
                  number: 8000
"""


def render_eks_public_ingress() -> str:
    return """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: visionflow-api
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
    alb.ingress.kubernetes.io/backend-protocol: HTTP
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: visionflow-api
                port:
                  number: 8000
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a VisionFlow ingress manifest.")
    parser.add_argument("--overlay", default="prod", choices=["prod", "eks-prod", "staging"])
    parser.add_argument("--host", default=os.getenv("VISIONFLOW_HOST", "").strip())
    parser.add_argument("--tls-secret-name", default=os.getenv("VISIONFLOW_TLS_SECRET_NAME", "visionflow-tls"))
    parser.add_argument("--certificate-arn", default=os.getenv("VISIONFLOW_ACM_CERTIFICATE_ARN", "").strip())
    parser.add_argument("--public-without-domain", action="store_true")
    args = parser.parse_args()

    if args.overlay == "eks-prod":
        if args.public_without_domain:
            print(render_eks_public_ingress(), end="")
            return 0
        if not args.host:
            print("VISIONFLOW_HOST or --host must be set.", file=sys.stderr)
            return 1
        if not args.certificate_arn:
            print("VISIONFLOW_ACM_CERTIFICATE_ARN or --certificate-arn must be set for eks-prod.", file=sys.stderr)
            return 1
        print(render_eks_ingress(args.host, args.certificate_arn), end="")
        return 0

    if not args.host:
        print("VISIONFLOW_HOST or --host must be set.", file=sys.stderr)
        return 1

    print(render_prod_ingress(args.host, args.tls_secret_name), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
