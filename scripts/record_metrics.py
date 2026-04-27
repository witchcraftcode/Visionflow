#!/usr/bin/env python3
import argparse
import json
import statistics
import time
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_PATH = ROOT_DIR / "METRICS_RESULTS.md"
DEFAULT_IMAGE_PATH = ROOT_DIR / "test.jpg"


def request_json(method, url, body=None, headers=None, timeout=10):
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def multipart_body(fields, file_field, file_path):
    boundary = f"----visionflow-{uuid.uuid4().hex}"
    chunks = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(str(value).encode())
        chunks.append(b"\r\n")

    data = Path(file_path).read_bytes()
    chunks.append(f"--{boundary}\r\n".encode())
    chunks.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{Path(file_path).name}"\r\n'.encode()
    )
    chunks.append(b"Content-Type: image/jpeg\r\n\r\n")
    chunks.append(data)
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * pct))
    return ordered[index]


def fmt_ms(value):
    return "n/a" if value is None else f"{value:.2f} ms"


def fmt_rate(value, unit):
    return "n/a" if value is None else f"{value:.2f} {unit}"


def wait_for_api(base_url, timeout_seconds):
    deadline = time.perf_counter() + timeout_seconds
    last_error = None
    while time.perf_counter() < deadline:
        try:
            return request_json("GET", f"{base_url}/health")
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"API did not become healthy within {timeout_seconds}s: {last_error}")


def collect_metrics(args):
    base_url = args.base_url.rstrip("/")
    health = wait_for_api(base_url, args.startup_timeout_seconds)
    ready_before = request_json("GET", f"{base_url}/ready")
    models = request_json("GET", f"{base_url}/models")

    job_ids = []
    enqueue_latencies_ms = []
    failed_submissions = []
    started = time.perf_counter()

    for _ in range(args.requests):
        body, headers = multipart_body({"model": args.model}, "file", args.image)
        t0 = time.perf_counter()
        try:
            response = request_json("POST", f"{base_url}/predict", body=body, headers=headers)
            enqueue_latencies_ms.append((time.perf_counter() - t0) * 1000)
            job_ids.append(response["job_id"])
        except Exception as exc:
            failed_submissions.append(str(exc))

    enqueue_finished = time.perf_counter()
    deadline = time.perf_counter() + args.poll_timeout_seconds
    terminal = {}

    while time.perf_counter() < deadline and len(terminal) < len(job_ids):
        for job_id in job_ids:
            if job_id in terminal:
                continue
            try:
                status = request_json("GET", f"{base_url}/status/{job_id}")
            except Exception:
                continue
            if status["status"] in {"completed", "failed", "timed_out", "dead_lettered"}:
                terminal[job_id] = status
        if len(terminal) < len(job_ids):
            time.sleep(args.poll_interval_seconds)

    completed_at = time.perf_counter()
    ready_after = request_json("GET", f"{base_url}/ready")
    metrics_text = request_text(f"{base_url}/metrics")

    statuses = {}
    durations_ms = []
    for status in terminal.values():
        statuses[status["status"]] = statuses.get(status["status"], 0) + 1
        if status.get("duration_ms") is not None:
            durations_ms.append(status["duration_ms"])

    enqueue_seconds = enqueue_finished - started
    completion_seconds = completed_at - started
    accepted = len(job_ids)
    completed = statuses.get("completed", 0)

    return {
        "label": args.label,
        "timestamp": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "base_url": base_url,
        "model": args.model,
        "image": str(Path(args.image).resolve()),
        "requests_attempted": args.requests,
        "health": health,
        "ready_before": ready_before,
        "ready_after": ready_after,
        "models": models.get("available_models", []),
        "accepted": accepted,
        "failed_submissions": len(failed_submissions),
        "enqueue_requests_per_second": accepted / enqueue_seconds if enqueue_seconds else None,
        "enqueue_avg_latency_ms": statistics.mean(enqueue_latencies_ms) if enqueue_latencies_ms else None,
        "enqueue_p95_latency_ms": percentile(enqueue_latencies_ms, 0.95),
        "enqueue_max_latency_ms": max(enqueue_latencies_ms) if enqueue_latencies_ms else None,
        "terminal_jobs": len(terminal),
        "statuses": statuses,
        "success_rate": completed / accepted if accepted else None,
        "completed_jobs_per_second": completed / completion_seconds if completion_seconds else None,
        "job_duration_avg_ms": statistics.mean(durations_ms) if durations_ms else None,
        "job_duration_p95_ms": percentile(durations_ms, 0.95),
        "metrics_lines": [line for line in metrics_text.splitlines() if line.startswith("visionflow_")],
    }


def render_entry(result):
    queue_depth = result["ready_after"].get("queue_depth", "n/a")
    dead_letter_depth = result["ready_after"].get("dead_letter_depth", "n/a")
    success_rate = result["success_rate"]
    success_rate_text = "n/a" if success_rate is None else f"{success_rate * 100:.2f}%"
    models_text = ", ".join(result["models"])

    return f"""
## {result["timestamp"]} {result["label"]}

### Environment
- Environment: running service at `{result["base_url"]}`
- Model tested: `{result["model"]}`
- Test image: `{result["image"]}`
- Prediction requests attempted: `{result["requests_attempted"]}`

### Results
| Metric | Result |
|---|---:|
| Requests accepted | {result["accepted"]} |
| Failed submissions | {result["failed_submissions"]} |
| Approx enqueue request rate | {fmt_rate(result["enqueue_requests_per_second"], "requests/sec")} |
| Average `POST /predict` enqueue latency | {fmt_ms(result["enqueue_avg_latency_ms"])} |
| p95 `POST /predict` enqueue latency | {fmt_ms(result["enqueue_p95_latency_ms"])} |
| Max `POST /predict` enqueue latency | {fmt_ms(result["enqueue_max_latency_ms"])} |
| Terminal jobs observed | {result["terminal_jobs"]} |
| Job success rate | {success_rate_text} |
| Completed-job throughput | {fmt_rate(result["completed_jobs_per_second"], "jobs/sec")} |
| Average job duration | {fmt_ms(result["job_duration_avg_ms"])} |
| p95 job duration | {fmt_ms(result["job_duration_p95_ms"])} |
| Queue depth after run | {queue_depth} |
| Dead-letter depth after run | {dead_letter_depth} |
| Available models | {len(result["models"])} ({models_text}) |

### SLO Target Status
| Target | Result | Status |
|---|---:|---|
| `POST /predict` p95 enqueue latency `< 300ms` | {fmt_ms(result["enqueue_p95_latency_ms"])} | {"Met" if result["enqueue_p95_latency_ms"] is not None and result["enqueue_p95_latency_ms"] < 300 else "Not met"} |
| Job completion success rate `>= 99%` | {success_rate_text} | {"Met" if success_rate is not None and success_rate >= 0.99 else "Not met"} |
| Queue backlog recovery within `15 min` | Queue depth `{queue_depth}` after run | {"Met for this run" if queue_depth == 0 else "Not met"} |
| Dead-letter queue growth alert | Dead-letter depth `{dead_letter_depth}` after run | {"No growth observed" if dead_letter_depth == 0 else "Growth observed"} |

### Failure and Retry Stats
- Job statuses: `{json.dumps(result["statuses"], sort_keys=True)}`
- Failed submissions: `{result["failed_submissions"]}`
- Dead-letter depth after run: `{dead_letter_depth}`
"""


def append_entry(path, entry):
    path = Path(path)
    existing = path.read_text() if path.exists() else "# VisionFlow Metrics and Results Log\n"
    path.write_text(existing.rstrip() + "\n\n" + entry.strip() + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run VisionFlow metrics probe and append results.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="resnet18")
    parser.add_argument("--image", default=str(DEFAULT_IMAGE_PATH))
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--label", default="Metrics Run")
    parser.add_argument("--results-file", default=str(DEFAULT_RESULTS_PATH))
    parser.add_argument("--startup-timeout-seconds", type=int, default=30)
    parser.add_argument("--poll-timeout-seconds", type=int, default=90)
    parser.add_argument("--poll-interval-seconds", type=float, default=0.25)
    parser.add_argument("--json", action="store_true", help="Print raw JSON result.")
    args = parser.parse_args()

    result = collect_metrics(args)
    append_entry(args.results_file, render_entry(result))

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Metrics appended to {args.results_file}")


if __name__ == "__main__":
    main()
