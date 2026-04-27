#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="${REGISTRY:-ghcr.io/witchcraftcode}"
TAG="${TAG:-latest}"
PUSH="false"
DOCKER_BIN="${DOCKER_BIN:-docker}"
PLATFORM="${PLATFORM:-}"

usage() {
  cat <<EOF
Usage: ./scripts/publish_images.sh [--registry REGISTRY] [--tag TAG] [--platform PLATFORM] [--push]

Examples:
  ./scripts/publish_images.sh
  REGISTRY=676766460202.dkr.ecr.us-east-1.amazonaws.com PLATFORM=linux/amd64 ./scripts/publish_images.sh --push
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --registry)
      REGISTRY="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    --push)
      PUSH="true"
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

API_IMAGE="${REGISTRY}/visionflow-api:${TAG}"
WORKER_IMAGE="${REGISTRY}/visionflow-worker:${TAG}"

echo "Building images:"
echo "  ${API_IMAGE}"
echo "  ${WORKER_IMAGE}"

if [ -n "${PLATFORM}" ]; then
  echo "Using platform: ${PLATFORM}"
fi

if [ "${PUSH}" = "true" ]; then
  BUILD_ARGS=("${DOCKER_BIN}" buildx build)
  if [ -n "${PLATFORM}" ]; then
    BUILD_ARGS+=(--platform "${PLATFORM}")
  fi
  "${BUILD_ARGS[@]}" --push -t "${API_IMAGE}" -f "${ROOT_DIR}/Dockerfile.api" "${ROOT_DIR}"
  "${BUILD_ARGS[@]}" --push -t "${WORKER_IMAGE}" -f "${ROOT_DIR}/Dockerfile.worker" "${ROOT_DIR}"
else
  BUILD_ARGS=("${DOCKER_BIN}" build)
  if [ -n "${PLATFORM}" ]; then
    BUILD_ARGS+=(--platform "${PLATFORM}")
  fi
  "${BUILD_ARGS[@]}" -t "${API_IMAGE}" -f "${ROOT_DIR}/Dockerfile.api" "${ROOT_DIR}"
  "${BUILD_ARGS[@]}" -t "${WORKER_IMAGE}" -f "${ROOT_DIR}/Dockerfile.worker" "${ROOT_DIR}"
fi

echo "Image publish helper completed."
