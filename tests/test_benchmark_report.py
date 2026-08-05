from scripts.run_benchmarks import render_report


def test_render_benchmark_report_contains_core_sections():
    report = render_report(
        [
            {
                "model": "resnet18",
                "concurrency": 5,
                "requests": 20,
                "throughput_rps": 10.5,
                "success_rate": 1.0,
                "p50_latency_ms": 42.0,
                "p95_latency_ms": 55.0,
                "p99_latency_ms": 60.0,
                "avg_job_duration_ms": 18.0,
                "statuses": {"completed": 20},
            }
        ],
        [
            {
                "model": "yolov5",
                "batch_size": 4,
                "requests": 10,
                "throughput_images_per_second": 25.0,
                "p95_batch_latency_ms": 70.0,
                "p99_batch_latency_ms": 80.0,
                "success_rate": 1.0,
                "avg_job_duration_ms": 22.0,
                "statuses": {"completed": 10},
            }
        ],
        [
            {
                "label": "onnx-cpu",
                "iterations": 10,
                "avg_latency_ms": 20.0,
                "p95_latency_ms": 30.0,
                "p99_latency_ms": 35.0,
            }
        ],
        [
            {
                "label": "onnx-cpu-batch",
                "batch_size": 4,
                "iterations": 10,
                "avg_latency_ms": 40.0,
                "p95_latency_ms": 50.0,
                "p99_latency_ms": 60.0,
            }
        ],
        ["GPU comparison skipped"],
    )

    assert "Concurrent Users" in report
    assert "Batch Size Comparisons" in report
    assert "ONNX vs Native Runtime" in report
    assert "resnet18" in report
    assert "p95" in report
    assert "GPU comparison skipped" in report
