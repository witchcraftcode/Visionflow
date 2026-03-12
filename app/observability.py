import json
import logging
import threading
import time
from collections import defaultdict

LOGGER = logging.getLogger("visionflow")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

_LOCK = threading.Lock()
_COUNTERS = defaultdict(float)
_HISTOGRAMS = defaultdict(list)
_GAUGES = {}


def log_event(event: str, **fields):
    payload = {"event": event, **fields}
    LOGGER.info(json.dumps(payload, sort_keys=True))


def normalize_metrics_path(path: str) -> str:
    if path.startswith("/status/"):
        return "/status/{job_id}"
    if path.startswith("/jobs/") and path.endswith("/cancel"):
        return "/jobs/{job_id}/cancel"
    if path.startswith("/models/") and path.endswith("/versions"):
        return "/models/{model_name}/versions"
    if path.startswith("/models/") and path.endswith("/promote"):
        return "/models/{model_name}/promote"
    return path


def _key(base: str, labels: dict):
    if not labels:
        return base
    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f"{base}{{{label_str}}}"


def track_http_metrics(method: str, path: str, status_code: int, start_time: float):
    normalized = normalize_metrics_path(path)
    labels = {"method": method, "path": normalized, "status_code": str(status_code)}
    latency_labels = {"method": method, "path": normalized}
    with _LOCK:
        _COUNTERS[_key("visionflow_http_requests_total", labels)] += 1.0
        _HISTOGRAMS[_key("visionflow_http_request_latency_seconds", latency_labels)].append(time.time() - start_time)


def track_job_status(status: str, model: str, model_version: str):
    labels = {"status": status, "model": model, "model_version": model_version}
    with _LOCK:
        _COUNTERS[_key("visionflow_jobs_total", labels)] += 1.0


def set_queue_depth(depth: int):
    with _LOCK:
        _GAUGES["visionflow_queue_depth"] = float(depth)


def set_dead_letter_depth(depth: int):
    with _LOCK:
        _GAUGES["visionflow_dead_letter_depth"] = float(depth)


def metrics_payload():
    lines = []
    with _LOCK:
        for key, value in sorted(_COUNTERS.items()):
            lines.append(f"{key} {value}")
        for key, values in sorted(_HISTOGRAMS.items()):
            if not values:
                continue
            total = sum(values)
            count = len(values)
            lines.append(f"{key}_count {count}")
            lines.append(f"{key}_sum {total}")
            lines.append(f"{key}_avg {total / count}")
        for key, value in sorted(_GAUGES.items()):
            lines.append(f"{key} {value}")
    payload = "\n".join(lines) + "\n"
    return payload.encode(), "text/plain; version=0.0.4"
