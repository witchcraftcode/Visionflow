from fastapi.testclient import TestClient
import pytest

from app import main as api
from app import security
from app.api.v1 import models as models_api


@pytest.fixture(autouse=True)
def bypass_security(monkeypatch):
    monkeypatch.setattr(security, "verify_api_key", lambda provided: True)
    monkeypatch.setattr(security, "allow_request", lambda client_id: True)
    monkeypatch.setattr(security, "verify_admin_key", lambda provided: True)


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

    monkeypatch.setattr(models_api.registry, "register_model_version", register_model_version)
    monkeypatch.setattr(models_api.registry, "promote_model_version", promote_model_version)
    monkeypatch.setattr(
        models_api,
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


def test_model_version_crud_routes(monkeypatch):
    update_calls = []
    delete_calls = []
    audit_calls = []

    monkeypatch.setattr(
        models_api.registry,
        "model_metadata",
        lambda model_name, version: {
            "name": model_name,
            "version": version,
            "default_version": "1.0.0",
            "runtime": "onnx",
            "artifact_uri": "app/models/onnx/custom.onnx",
            "class": "app.models.onnx_model.ONNXVisionModel",
            "input_schema": {"type": "image"},
            "output_schema": {"type": "classification"},
            "resources": {},
        },
    )
    monkeypatch.setattr(
        models_api.registry,
        "update_model_version",
        lambda model_name, version, payload: update_calls.append((model_name, version, payload)),
    )
    monkeypatch.setattr(
        models_api.registry,
        "delete_model_version",
        lambda model_name, version: delete_calls.append((model_name, version)),
    )
    monkeypatch.setattr(
        models_api,
        "record_admin_audit_event",
        lambda action, **fields: audit_calls.append((action, fields)),
    )

    client = TestClient(api.app)
    get_resp = client.get("/models/custom/versions/1.0.0")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "custom"

    update_resp = client.put(
        "/models/custom/versions/1.0.0",
        json={"artifact_uri": "app/models/onnx/custom-v2.onnx"},
    )
    assert update_resp.status_code == 200
    assert update_calls[0][0:2] == ("custom", "1.0.0")
    assert update_calls[0][2]["artifact_uri"] == "app/models/onnx/custom-v2.onnx"

    delete_resp = client.delete("/models/custom/versions/1.0.0")
    assert delete_resp.status_code == 200
    assert delete_calls == [("custom", "1.0.0")]
    assert [event[0] for event in audit_calls] == ["model_version_updated", "model_version_deleted"]
