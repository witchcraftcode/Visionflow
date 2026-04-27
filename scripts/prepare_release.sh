#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OVERLAY="prod"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/visionflow-release}"
APPLY="false"
NAMESPACE="${K8S_NAMESPACE:-visionflow-prod}"
PYTHON_BIN="${PYTHON_BIN:-}"
PUBLIC_WITHOUT_DOMAIN="false"

usage() {
  cat <<EOF
Usage: ./scripts/prepare_release.sh [--overlay prod|eks-prod] [--output-dir DIR] [--apply] [--public-without-domain]

Required environment:
  VISIONFLOW_API_KEY
  VISIONFLOW_ADMIN_API_KEY
  VISIONFLOW_HOST

Additional required environment for eks-prod:
  VISIONFLOW_ACM_CERTIFICATE_ARN

Optional environment:
  VISIONFLOW_TLS_SECRET_NAME
  K8S_NAMESPACE
  KUBECTL_BIN
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --overlay)
      OVERLAY="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --apply)
      APPLY="true"
      shift 1
      ;;
    --public-without-domain)
      PUBLIC_WITHOUT_DOMAIN="true"
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ -z "${VISIONFLOW_API_KEY:-}" ] || [ -z "${VISIONFLOW_ADMIN_API_KEY:-}" ]; then
  echo "VISIONFLOW_API_KEY and VISIONFLOW_ADMIN_API_KEY must be set." >&2
  exit 1
fi

if [ "${PUBLIC_WITHOUT_DOMAIN}" != "true" ] && [ -z "${VISIONFLOW_HOST:-}" ]; then
  echo "VISIONFLOW_HOST must be set unless --public-without-domain is used." >&2
  exit 1
fi

if [ "${OVERLAY}" = "eks-prod" ] && [ "${PUBLIC_WITHOUT_DOMAIN}" != "true" ] && [ -z "${VISIONFLOW_ACM_CERTIFICATE_ARN:-}" ]; then
  echo "VISIONFLOW_ACM_CERTIFICATE_ARN must be set for eks-prod." >&2
  exit 1
fi

if [ "${OVERLAY}" != "eks-prod" ] && [ "${PUBLIC_WITHOUT_DOMAIN}" = "true" ]; then
  echo "--public-without-domain is only supported for eks-prod." >&2
  exit 1
fi

if [ -z "${PYTHON_BIN}" ]; then
  if [ -x "${ROOT_DIR}/.venv/bin/python" ]; then
    PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  else
    echo "Python is required to prepare release artifacts." >&2
    exit 1
  fi
fi

mkdir -p "${OUTPUT_DIR}"

SECRET_FILE="${OUTPUT_DIR}/visionflow-secret.yaml"
INGRESS_FILE="${OUTPUT_DIR}/visionflow-ingress.yaml"
KUBECTL_BIN="${KUBECTL_BIN:-kubectl}"

"${PYTHON_BIN}" "${ROOT_DIR}/scripts/render_k8s_secret.py" --namespace "${NAMESPACE}" > "${SECRET_FILE}"
if [ "${PUBLIC_WITHOUT_DOMAIN}" = "true" ]; then
  "${PYTHON_BIN}" "${ROOT_DIR}/scripts/render_ingress.py" --overlay "${OVERLAY}" --public-without-domain > "${INGRESS_FILE}"
  "${PYTHON_BIN}" "${ROOT_DIR}/scripts/validate_deployment.py" --overlay "${OVERLAY}" --ingress-file "${INGRESS_FILE}" --secret-file "${SECRET_FILE}" --allow-missing-host --allow-missing-tls
else
  "${PYTHON_BIN}" "${ROOT_DIR}/scripts/render_ingress.py" --overlay "${OVERLAY}" > "${INGRESS_FILE}"
  "${PYTHON_BIN}" "${ROOT_DIR}/scripts/validate_deployment.py" --overlay "${OVERLAY}" --ingress-file "${INGRESS_FILE}" --secret-file "${SECRET_FILE}"
fi

echo "Prepared release artifacts:"
echo "  Secret:  ${SECRET_FILE}"
echo "  Ingress: ${INGRESS_FILE}"
echo
echo "Apply commands:"
echo "  ${KUBECTL_BIN} apply -f ${ROOT_DIR}/k8s/namespaces.yaml"
echo "  ${KUBECTL_BIN} apply -f ${SECRET_FILE}"
echo "  ${KUBECTL_BIN} apply -k ${ROOT_DIR}/k8s/overlays/${OVERLAY}"
echo "  ${KUBECTL_BIN} apply -f ${INGRESS_FILE}"

if [ "${APPLY}" = "true" ]; then
  "${KUBECTL_BIN}" apply -f "${ROOT_DIR}/k8s/namespaces.yaml"
  "${KUBECTL_BIN}" apply -f "${SECRET_FILE}"
  "${KUBECTL_BIN}" apply -k "${ROOT_DIR}/k8s/overlays/${OVERLAY}"
  "${KUBECTL_BIN}" apply -f "${INGRESS_FILE}"
  echo
  echo "Release manifests applied."
fi
