#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://localhost:8000}"
MODEL="${MODEL:-resnet18}"
IMAGE_PATH="${IMAGE_PATH:-${ROOT_DIR}/test.jpg}"
API_KEY="${VISIONFLOW_API_KEY:-}"
HOST_HEADER="${VISIONFLOW_HOST_HEADER:-}"
POLL_TIMEOUT_SECONDS="${POLL_TIMEOUT_SECONDS:-30}"
STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-30}"

if [ ! -f "${IMAGE_PATH}" ]; then
  echo "Smoke test image not found: ${IMAGE_PATH}" >&2
  exit 1
fi

headers=(-H "Accept: application/json")
if [ -n "${API_KEY}" ]; then
  headers+=(-H "X-API-Key: ${API_KEY}")
fi
if [ -n "${HOST_HEADER}" ]; then
  headers+=(-H "Host: ${HOST_HEADER}")
fi

request() {
  local method="$1"
  local path="$2"
  shift 2
  curl --fail --silent --show-error -X "${method}" "${headers[@]}" "$@" "${BASE_URL}${path}"
}

python_json() {
  local script="$1"
  python3 -c "${script}"
}

wait_for_status() {
  local job_id="$1"
  local deadline=$((SECONDS + POLL_TIMEOUT_SECONDS))
  while [ "${SECONDS}" -lt "${deadline}" ]; do
    local status_payload
    status_payload="$(request GET "/status/${job_id}")"
    local status
    status="$(printf '%s' "${status_payload}" | python_json 'import json,sys; print(json.load(sys.stdin)["status"])')"
    if [ "${status}" = "completed" ] || [ "${status}" = "failed" ] || [ "${status}" = "timed_out" ] || [ "${status}" = "dead_lettered" ]; then
      printf '%s' "${status_payload}"
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for job ${job_id}" >&2
  return 1
}

wait_for_api() {
  local deadline=$((SECONDS + STARTUP_TIMEOUT_SECONDS))
  while [ "${SECONDS}" -lt "${deadline}" ]; do
    if curl --silent --show-error --output /dev/null "${BASE_URL}/health"; then
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for API at ${BASE_URL}" >&2
  return 1
}

wait_for_api

echo "Checking /health"
health_payload="$(request GET /health)"
printf '%s' "${health_payload}" | python_json 'import json,sys; assert json.load(sys.stdin)["status"] == "ok"'

echo "Checking /ready"
ready_payload="$(request GET /ready)"
printf '%s' "${ready_payload}" | python_json 'import json,sys; body=json.load(sys.stdin); assert body["status"] in {"ok","degraded"}'

echo "Checking /models"
models_payload="$(request GET /models)"
printf '%s' "${models_payload}" | python_json "import json,sys; body=json.load(sys.stdin); assert '${MODEL}' in body['available_models']"

echo "Submitting prediction job"
predict_payload="$(curl --fail --silent --show-error -X POST "${headers[@]}" -F "model=${MODEL}" -F "file=@${IMAGE_PATH}" "${BASE_URL}/predict")"
job_id="$(printf '%s' "${predict_payload}" | python_json 'import json,sys; body=json.load(sys.stdin); assert body["status"] == "queued"; print(body["job_id"])')"

echo "Waiting for job ${job_id}"
final_status_payload="$(wait_for_status "${job_id}")"
printf '%s' "${final_status_payload}" | python_json 'import json,sys; body=json.load(sys.stdin); assert body["status"] == "completed"; assert "result" in body and body["result"] is not None'

echo "Submitting cancellable job"
cancel_payload="$(curl --fail --silent --show-error -X POST "${headers[@]}" -F "model=${MODEL}" -F "file=@${IMAGE_PATH}" "${BASE_URL}/predict")"
cancel_job_id="$(printf '%s' "${cancel_payload}" | python_json 'import json,sys; print(json.load(sys.stdin)["job_id"])')"
cancel_status_payload="$(request POST "/jobs/${cancel_job_id}/cancel")"
printf '%s' "${cancel_status_payload}" | python_json 'import json,sys; body=json.load(sys.stdin); assert body["status"] in {"cancel_requested", "completed", "failed", "timed_out", "dead_lettered"}'

echo "Smoke test passed."
