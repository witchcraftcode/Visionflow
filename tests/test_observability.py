from app import observability


def test_observability_records_model_and_worker_metrics():
    observability._COUNTERS.clear()
    observability._HISTOGRAMS.clear()
    observability._GAUGES.clear()

    observability.track_http_metrics("GET", "/models", 500, 0.0)
    observability.track_model_inference("resnet18", "1.0.0", 12.5)
    observability.track_queue_wait("resnet18", "1.0.0", 3.0)
    observability.set_worker_utilization(cpu_percent=12.0, memory_percent=30.0, gpu_percent=0.0)
    observability.set_worker_health(last_recovery_count=2, stale_jobs_detected=1)

    payload, content_type = observability.metrics_payload()
    text = payload.decode()

    assert content_type == "text/plain; version=0.0.4"
    assert "visionflow_failed_requests_total" in text
    assert "visionflow_model_inference_duration_ms_avg" in text
    assert "visionflow_queue_wait_duration_ms_avg" in text
    assert "visionflow_worker_cpu_utilization_percent" in text
    assert "visionflow_worker_last_recovery_count" in text
