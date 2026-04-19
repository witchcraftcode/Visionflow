from fastapi.testclient import TestClient
import pytest

from app import main as api


@pytest.fixture(autouse=True)
def bypass_security(monkeypatch):
    monkeypatch.setattr(api, "verify_api_key", lambda provided: True)
    monkeypatch.setattr(api, "allow_request", lambda client_id: True)
    monkeypatch.setattr(api, "verify_admin_key", lambda provided: True)


def test_model_versions_unknown():
    client = TestClient(api.app)
    resp = client.get("/models/unknown/versions")
    assert resp.status_code == 404


def test_register_and_promote_model(monkeypatch):
    register_calls = []
    promote_calls = []
    audit_calls = []

    def register_model_version(model_name, version, payload):
        register_calls.append((model_name, version, payload))

    def promote_model_version(model_name, version):
        promote_calls.append((model_name, version))

    monkeypatch.setattr(api, "register_model_version", register_model_version)
    monkeypatch.setattr(api, "promote_model_version", promote_model_version)
    monkeypatch.setattr(
        api,
        "record_admin_audit_event",
        lambda action, **fields: audit_calls.append((action, fields)),
    )

    client = TestClient(api.app)
    register_resp = client.post(
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
    assert register_resp.status_code == 200
    assert register_calls[0][0] == "custom"
    assert register_calls[0][1] == "1.0.0"
    assert audit_calls[0][0] == "model_registered"

    promote_resp = client.post("/models/custom/promote", json={"version": "1.0.0"})
    assert promote_resp.status_code == 200
    assert promote_calls[0] == ("custom", "1.0.0")
    assert audit_calls[1][0] == "model_promoted"
