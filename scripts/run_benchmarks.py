#!/usr/bin/env python3
import argparse
import json
import statistics
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import onnxruntime as ort

from app.config import load_model_config
from app.models.adapter import VisionModelAdapter
from app.models.yolov5 import YOLOv5Model
from app.models.yolov5_native import NativeYOLOv5Model


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_PATH = ROOT_DIR / "BENCHMARK_RESULTS.md"
DEFAULT_IMAGE_PATH = ROOT_DIR / "test.jpg"


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * pct))))
    return ordered[index]


def request_json(method, url, body=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def multipart_body(fields, file_field, file_paths):
    boundary = f"----visionflow-benchmark-{uuid.uuid4().hex}"
    chunks = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(str(value).encode())
        chunks.append(b"\r\n")
    for file_path in file_paths:
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{file_field}"; filename="{Path(file_path).name}"\r\n'.encode())
        chunks.append(b"Content-Type: image/jpeg\r\n\r\n")
        chunks.append(Path(file_path).read_bytes())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def await_terminal_status(base_url, job_id, timeout_seconds):
    deadline = time.perf_counter() + timeout_seconds
    while time.perf_counter() < deadline:
        payload = request_json("GET", f"{base_url}/status/{job_id}")
        if payload["status"] in {"completed", "failed", "timed_out", "dead_lettered"}:
            return payload
        time.sleep(0.1)
    raise TimeoutError(f"Job {job_id} did not reach a terminal state")


def run_single_request(base_url, model, image, timeout_seconds):
    body, headers = multipart_body({"model": model}, "file", [image])
    started = time.perf_counter()
    queued = request_json("POST", f"{base_url}/predict", body=body, headers=headers, timeout=timeout_seconds)
    terminal = await_terminal_status(base_url, queued["job_id"], timeout_seconds)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return elapsed_ms, terminal


def run_concurrency_scenario(base_url, model, image, concurrency, requests, timeout_seconds):
    started = time.perf_counter()
    latencies = []
    statuses = {}
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(run_single_request, base_url, model, image, timeout_seconds) for _ in range(requests)]
        for future in as_completed(futures):
            elapsed_ms, terminal = future.result()
            latencies.append(elapsed_ms)
            statuses[terminal["status"]] = statuses.get(terminal["status"], 0) + 1
    elapsed = time.perf_counter() - started
    return {
        "model": model,
        "concurrency": concurrency,
        "requests": requests,
        "throughput_rps": requests / elapsed if elapsed else 0.0,
        "p95_latency_ms": percentile(latencies, 0.95) or 0.0,
        "p99_latency_ms": percentile(latencies, 0.99) or 0.0,
        "success_rate": statuses.get("completed", 0) / requests if requests else 0.0,
        "statuses": statuses,
    }


def run_batch_http_scenario(base_url, model, image, batch_size, requests, timeout_seconds):
    latencies = []
    statuses = {}
    started = time.perf_counter()
    for _ in range(requests):
        body, headers = multipart_body({"model": model}, "files", [image] * batch_size)
        queued = request_json("POST", f"{base_url}/predict/batch", body=body, headers=headers, timeout=timeout_seconds)
        t0 = time.perf_counter()
        terminal = await_terminal_status(base_url, queued["job_id"], timeout_seconds)
        latencies.append((time.perf_counter() - t0) * 1000)
        statuses[terminal["status"]] = statuses.get(terminal["status"], 0) + 1
    elapsed = time.perf_counter() - started
    return {
        "model": model,
        "batch_size": batch_size,
        "requests": requests,
        "throughput_images_per_second": (batch_size * requests) / elapsed if elapsed else 0.0,
        "p95_batch_latency_ms": percentile(latencies, 0.95) or 0.0,
        "p99_batch_latency_ms": percentile(latencies, 0.99) or 0.0,
        "success_rate": statuses.get("completed", 0) / requests if requests else 0.0,
        "statuses": statuses,
    }


def benchmark_runtime(label, adapter, image_path, iterations):
    image_bytes = Path(image_path).read_bytes()
    latencies = []
    for _ in range(iterations):
        started = time.perf_counter()
        adapter.predict(image_bytes)
        latencies.append((time.perf_counter() - started) * 1000)
    return {
        "label": label,
        "iterations": iterations,
        "avg_latency_ms": statistics.mean(latencies),
        "p95_latency_ms": percentile(latencies, 0.95) or 0.0,
        "p99_latency_ms": percentile(latencies, 0.99) or 0.0,
    }


def benchmark_batch_runtime(label, adapter, image_path, batch_size, iterations):
    image_bytes_list = [Path(image_path).read_bytes()] * batch_size
    latencies = []
    for _ in range(iterations):
        started = time.perf_counter()
        adapter.predict_batch(image_bytes_list)
        latencies.append((time.perf_counter() - started) * 1000)
    return {
        "label": label,
        "batch_size": batch_size,
        "iterations": iterations,
        "avg_latency_ms": statistics.mean(latencies),
        "p95_latency_ms": percentile(latencies, 0.95) or 0.0,
        "p99_latency_ms": percentile(latencies, 0.99) or 0.0,
    }


def runtime_comparisons(image_path, iterations):
    config = load_model_config("yolov5")
    comparisons = []
    unavailable = []

    comparisons.append(
        benchmark_runtime("onnx-cpu", VisionModelAdapter(YOLOv5Model(providers=["CPUExecutionProvider"]), config), image_path, iterations)
    )

    if "CUDAExecutionProvider" in ort.get_available_providers():
        comparisons.append(
            benchmark_runtime(
                "onnx-gpu",
                VisionModelAdapter(YOLOv5Model(providers=["CUDAExecutionProvider", "CPUExecutionProvider"]), config),
                image_path,
                iterations,
            )
        )
    else:
        unavailable.append("onnx-gpu unavailable: CUDAExecutionProvider not present in this environment")

    try:
        comparisons.append(benchmark_runtime("native-cpu", VisionModelAdapter(NativeYOLOv5Model(device="cpu"), config), image_path, iterations))
    except Exception as exc:
        unavailable.append(f"native-cpu unavailable: {exc}")

    try:
        import torch

        if torch.cuda.is_available():
            comparisons.append(
                benchmark_runtime("native-gpu", VisionModelAdapter(NativeYOLOv5Model(device="cuda"), config), image_path, iterations)
            )
        else:
            unavailable.append("native-gpu unavailable: torch CUDA is not available")
    except Exception as exc:
        unavailable.append(f"native-gpu unavailable: {exc}")

    return comparisons, unavailable


def batch_runtime_comparisons(image_path, iterations, batch_sizes):
    config = load_model_config("yolov5")
    adapter = VisionModelAdapter(YOLOv5Model(providers=["CPUExecutionProvider"]), config)
    return [benchmark_batch_runtime("onnx-cpu-batch", adapter, image_path, batch_size, iterations) for batch_size in batch_sizes]


def render_report(concurrency_results, batch_http_results, runtime_results, batch_runtime_results, unavailable_notes):
    lines = [
        "# VisionFlow Benchmark Report",
        "",
        f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        "",
        "## Concurrent Users",
        "",
        "| Model | Concurrency | Requests | Throughput (req/s) | p95 (ms) | p99 (ms) | Success Rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for entry in concurrency_results:
        lines.append(
            f"| {entry['model']} | {entry['concurrency']} | {entry['requests']} | {entry['throughput_rps']:.2f} | {entry['p95_latency_ms']:.2f} | {entry['p99_latency_ms']:.2f} | {entry['success_rate'] * 100:.2f}% |"
        )

    lines.extend(["", "## Batch Size Comparisons", "", "| Model | Batch Size | Requests | Images/sec | p95 Batch Latency (ms) | p99 Batch Latency (ms) | Success Rate |", "|---|---:|---:|---:|---:|---:|---:|"])
    for entry in batch_http_results:
        lines.append(
            f"| {entry['model']} | {entry['batch_size']} | {entry['requests']} | {entry['throughput_images_per_second']:.2f} | {entry['p95_batch_latency_ms']:.2f} | {entry['p99_batch_latency_ms']:.2f} | {entry['success_rate'] * 100:.2f}% |"
        )

    lines.extend(["", "## ONNX vs Native Runtime", "", "| Runtime | Iterations | Avg Latency (ms) | p95 (ms) | p99 (ms) |", "|---|---:|---:|---:|---:|"])
    for entry in runtime_results:
        lines.append(
            f"| {entry['label']} | {entry['iterations']} | {entry['avg_latency_ms']:.2f} | {entry['p95_latency_ms']:.2f} | {entry['p99_latency_ms']:.2f} |"
        )

    lines.extend(["", "## Batch Runtime Microbenchmarks", "", "| Runtime | Batch Size | Iterations | Avg Latency (ms) | p95 (ms) | p99 (ms) |", "|---|---:|---:|---:|---:|---:|"])
    for entry in batch_runtime_results:
        lines.append(
            f"| {entry['label']} | {entry['batch_size']} | {entry['iterations']} | {entry['avg_latency_ms']:.2f} | {entry['p95_latency_ms']:.2f} | {entry['p99_latency_ms']:.2f} |"
        )

    lines.extend(["", "## Availability Notes", ""])
    for note in unavailable_notes:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Run VisionFlow live benchmark suites.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--image", default=str(DEFAULT_IMAGE_PATH))
    parser.add_argument("--concurrency", nargs="+", type=int, default=[1, 5, 10, 20])
    parser.add_argument("--requests-per-scenario", type=int, default=10)
    parser.add_argument("--batch-sizes", nargs="+", type=int, default=[1, 2, 4, 8])
    parser.add_argument("--runtime-iterations", type=int, default=10)
    parser.add_argument("--results-file", default=str(DEFAULT_RESULTS_PATH))
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    concurrency_results = []
    for model in ("resnet18", "mobilenet"):
        for concurrency in args.concurrency:
            concurrency_results.append(run_concurrency_scenario(base_url, model, args.image, concurrency, args.requests_per_scenario, args.timeout_seconds))

    batch_http_results = [
        run_batch_http_scenario(base_url, "yolov5", args.image, batch_size, args.requests_per_scenario, args.timeout_seconds)
        for batch_size in args.batch_sizes
    ]
    runtime_results, unavailable_notes = runtime_comparisons(args.image, args.runtime_iterations)
    batch_runtime_results = batch_runtime_comparisons(args.image, args.runtime_iterations, args.batch_sizes)
    Path(args.results_file).write_text(render_report(concurrency_results, batch_http_results, runtime_results, batch_runtime_results, unavailable_notes))
    print(f"Benchmark report written to {args.results_file}")


if __name__ == "__main__":
    main()
