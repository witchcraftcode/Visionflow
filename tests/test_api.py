from fastapi.testclient import TestClient
import pytest

from app import main as api
from app import security
from app.api.v1 import health as health_api
from app.api.v1 import models as models_api
from app.services import inference
from app.services.queue import QueueService


class InMemoryQueueBackend:
    def __init__(self, store=None):
        self.store = {} if store is None else store
        self.enqueued = []
        self.dead_lettered = []
        self.idempotency = {}

    def enqueue_job(self, job_id: str):
        self.enqueued.append(job_id)

    def enqueue_dead_letter(self, job_id: str):
        self.dead_lettered.append(job_id)

    def dequeue_job(self):
        return self.enqueued.pop(0)

    def set_job(self, job_id: str, data: dict):
        self.store[job_id] = data

    def get_job(self, job_id: str):
        return self.store.get(job_id)

    def iter_jobs(self):
        return iter(self.store.items())

    def set_idempotency_job(self, key: str, job_id: str):
        self.idempotency[key] = job_id

    def get_idempotency_job(self, key: str):
        return self.idempotency.get(key)

    def queue_depth(self) -> int:
        return len(self.enqueued)

    def dead_letter_depth(self) -> int:
        return len(self.dead_lettered)

    def ping(self) -> bool:
        return True


def use_memory_queue(monkeypatch, store=None):
    backend = InMemoryQueueBackend(store=store)
    service = QueueService(backend)
    monkeypatch.setattr(inference.queue, "queue_service", service)
    return backend


@pytest.fixture(autouse=True)
def bypass_security(monkeypatch):
    monkeypatch.setattr(security, "verify_api_key", lambda provided: True)
    monkeypatch.setattr(security, "allow_request", lambda client_id: True)
    monkeypatch.setattr(security, "verify_admin_key", lambda provided: True)


def test_health():
    client = TestClient(api.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    versioned_resp = client.get("/api/v1/health")
    assert versioned_resp.status_code == 200
    assert versioned_resp.json() == {"status": "ok"}


def test_ready(monkeypatch):
    monkeypatch.setattr(health_api.queue, "ping", lambda: True)
    monkeypatch.setattr(health_api.queue, "queue_depth", lambda: 2)
    monkeypatch.setattr(health_api.queue, "dead_letter_depth", lambda: 1)
    client = TestClient(api.app)
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["queue_depth"] == 2
    assert resp.json()["dead_letter_depth"] == 1


def test_models():
    client = TestClient(api.app)
    resp = client.get("/models")
    assert resp.status_code == 200
    body = resp.json()
    assert "available_models" in body
    assert isinstance(body["available_models"], list)
    assert "resnet18" in body["available_models"]
    assert "models" in body


def test_predict_and_status(monkeypatch):
    backend = use_memory_queue(monkeypatch)
    monkeypatch.setattr(inference.registry, "resolve_model_version", lambda model, version: "1.0.0")

    client = TestClient(api.app)

    resp = client.post(
        "/predict",
        data={"model": "resnet18"},
        files={"file": ("x.jpg", b"fake", "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "queued"
    assert body["job_id"] in backend.enqueued
    assert body["model_version"] == "1.0.0"
    assert body["batch_count"] == 1

    status_resp = client.get(f"/status/{body['job_id']}")
    assert status_resp.status_code == 200
    status_body = status_resp.json()
    assert status_body["status"] == "queued"
    assert status_body["model"] == "resnet18"
    assert status_body["model_version"] == "1.0.0"
    assert status_body["job_id"] == body["job_id"]
    assert "image_bytes" not in status_body


def test_predict_batch_and_status(monkeypatch):
    backend = use_memory_queue(monkeypatch)
    monkeypatch.setattr(inference.registry, "resolve_model_version", lambda model, version: "1.0.0")

    client = TestClient(api.app)
    resp = client.post(
        "/predict/batch",
        data={"model": "resnet18"},
        files=[
            ("files", ("a.jpg", b"one", "image/jpeg")),
            ("files", ("b.jpg", b"two", "image/jpeg")),
        ],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["batch_count"] == 2
    assert body["job_id"] in backend.enqueued
    assert "image_bytes_list" in backend.store[body["job_id"]]


def test_status_missing_job(monkeypatch):
    use_memory_queue(monkeypatch)
    client = TestClient(api.app)
    resp = client.get("/status/does-not-exist")
    assert resp.status_code == 404
    payload = resp.json()
    assert payload["error"]["code"] == "http_error"


def test_predict_rejects_bad_content_type():
    client = TestClient(api.app)
    resp = client.post(
        "/predict",
        data={"model": "resnet18"},
        files={"file": ("x.txt", b"fake", "text/plain")},
    )
    assert resp.status_code == 415


def test_predict_idempotency_reuse(monkeypatch):
    store = {
        "job-1": {
            "job_id": "job-1",
            "status": "queued",
            "model": "resnet18",
            "model_version": "1.0.0",
            "image_bytes": "00",
            "result": None,
            "error": None,
        }
    }
    backend = use_memory_queue(monkeypatch, store=store)
    backend.idempotency["abc"] = "job-1"
    monkeypatch.setattr(inference.registry, "has_model", lambda model, version=None: True)
    client = TestClient(api.app)
    resp = client.post(
        "/predict",
        data={"model": "resnet18"},
        files={"file": ("x.jpg", b"fake", "image/jpeg")},
        headers={"Idempotency-Key": "abc"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["idempotency_reused"] is True
    assert body["job_id"] == "job-1"


def test_cancel_job(monkeypatch):
    store = {
        "job-1": {
            "job_id": "job-1",
            "status": "queued",
            "model": "resnet18",
            "model_version": "1.0.0",
            "cancel_requested": False,
        }
    }
    use_memory_queue(monkeypatch, store=store)
    client = TestClient(api.app)
    resp = client.post("/jobs/job-1/cancel")
    assert resp.status_code == 200
    assert resp.json()["cancel_requested"] is True
    assert store["job-1"]["status"] == "cancel_requested"


def test_metrics_endpoint():
    client = TestClient(api.app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "visionflow_http_requests_total" in resp.text


def test_admin_audit_endpoint(monkeypatch):
    monkeypatch.setattr(
        models_api,
        "list_admin_audit_events",
        lambda limit=50: [{"action": "model_registered", "model": "resnet18", "version": "1.0.0"}],
    )
    client = TestClient(api.app)
    resp = client.get("/admin/audit?limit=5")
    assert resp.status_code == 200
    assert resp.json()["events"][0]["action"] == "model_registered"


def test_auth_rejection(monkeypatch):
    monkeypatch.setattr(security, "verify_api_key", lambda provided: False)
    client = TestClient(api.app)
    resp = client.get("/models")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_rate_limit_rejection(monkeypatch):
    monkeypatch.setattr(security, "verify_api_key", lambda provided: True)
    monkeypatch.setattr(security, "allow_request", lambda client_id: False)
    client = TestClient(api.app)
    resp = client.get("/models")
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limited"


def test_admin_rejection_for_register(monkeypatch):
    monkeypatch.setattr(security, "verify_api_key", lambda provided: True)
    monkeypatch.setattr(security, "allow_request", lambda client_id: True)
    monkeypatch.setattr(security, "verify_admin_key", lambda provided: False)
    client = TestClient(api.app)
    resp = client.post(
        "/models/register",
        json={
            "model": "custom",
            "version": "1.0.0",
            "runtime": "onnx",
            "artifact_uri": "app/models/onnx/custom.onnx",
            "class_path": "app.models.onnx_model.ONNXVisionModel",
            "input_schema": {"type": "image"},
            "output_schema": {"type": "classification"},
            "resources": {"cpu": "500m", "memory": "512Mi"},
        },
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


def test_admin_rejection_for_promote(monkeypatch):
    monkeypatch.setattr(security, "verify_api_key", lambda provided: True)
    monkeypatch.setattr(security, "allow_request", lambda client_id: True)
    monkeypatch.setattr(security, "verify_admin_key", lambda provided: False)
    client = TestClient(api.app)
    resp = client.post("/models/resnet18/promote", json={"version": "1.0.0"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


def test_drift_monitor_endpoints():
    client = TestClient(api.app)
    baseline_resp = client.post(
        "/monitoring/drift/baseline",
        json={"baseline": {"f1": {"mean": 0.0, "std": 1.0}}},
    )
    assert baseline_resp.status_code == 200

    observe_resp = client.post(
        "/monitoring/drift/observe",
        json={"features": {"f1": 5.0}, "label": "cat"},
    )
    assert observe_resp.status_code == 200

    summary_resp = client.get("/monitoring/drift/summary")
    assert summary_resp.status_code == 200
    body = summary_resp.json()
    assert "feature_drift" in body
    assert "prediction_distribution" in body
