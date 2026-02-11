from fastapi.testclient import TestClient
import types

from app import main as api


def test_health():
    client = TestClient(api.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_models():
    client = TestClient(api.app)
    resp = client.get("/models")
    assert resp.status_code == 200
    body = resp.json()
    assert "available_models" in body
    assert isinstance(body["available_models"], list)
    assert "resnet18" in body["available_models"]


def test_predict_and_status(monkeypatch):
    store = {}
    enqueued = []

    def set_job(job_id, data):
        store[job_id] = data

    def get_job(job_id):
        return store.get(job_id)

    def enqueue_job(job_id):
        enqueued.append(job_id)

    monkeypatch.setattr(api, "set_job", set_job)
    monkeypatch.setattr(api, "get_job", get_job)
    monkeypatch.setattr(api, "enqueue_job", enqueue_job)

    client = TestClient(api.app)

    resp = client.post(
        "/predict",
        data={"model": "resnet18"},
        files={"file": ("x.jpg", b"fake", "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "queued"
    assert body["job_id"] in enqueued

    status_resp = client.get(f"/status/{body['job_id']}")
    assert status_resp.status_code == 200
    status_body = status_resp.json()
    assert status_body["status"] == "queued"
    assert status_body["model"] == "resnet18"
    assert "image_bytes" not in status_body


def test_status_missing_job(monkeypatch):
    def get_job(job_id):
        return None

    monkeypatch.setattr(api, "get_job", get_job)
    client = TestClient(api.app)
    resp = client.get("/status/does-not-exist")
    assert resp.status_code == 404
