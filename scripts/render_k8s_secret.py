import argparse
import os
import sys


def build_secret_manifest(namespace: str, secret_name: str, api_key: str, admin_api_key: str) -> str:
    return f"""apiVersion: v1
kind: Secret
metadata:
  name: {secret_name}
  namespace: {namespace}
type: Opaque
stringData:
  api_key: "{api_key}"
  admin_api_key: "{admin_api_key}"
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a VisionFlow Kubernetes secret manifest.")
    parser.add_argument("--namespace", default=os.getenv("K8S_NAMESPACE", "visionflow-prod"))
    parser.add_argument("--name", default=os.getenv("K8S_SECRET_NAME", "visionflow-secrets"))
    args = parser.parse_args()

    api_key = os.getenv("VISIONFLOW_API_KEY", "").strip()
    admin_api_key = os.getenv("VISIONFLOW_ADMIN_API_KEY", "").strip()
    if not api_key or not admin_api_key:
        print("VISIONFLOW_API_KEY and VISIONFLOW_ADMIN_API_KEY must both be set.", file=sys.stderr)
        return 1

    print(build_secret_manifest(args.namespace, args.name, api_key, admin_api_key), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
