from fastapi.testclient import TestClient

from app import main as api


def test_model_versions_unknown():
    client = TestClient(api.app)
    resp = client.get("/models/unknown/versions")
    assert resp.status_code == 404


def test_register_and_promote_model(monkeypatch):
    register_calls = []
    promote_calls = []

    def register_model_version(model_name, version, payload):
        register_calls.append((model_name, version, payload))

    def promote_model_version(model_name, version):
        promote_calls.append((model_name, version))

    monkeypatch.setattr(api, "register_model_version", register_model_version)
    monkeypatch.setattr(api, "promote_model_version", promote_model_version)

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

    promote_resp = client.post("/models/custom/promote", json={"version": "1.0.0"})
    assert promote_resp.status_code == 200
    assert promote_calls[0] == ("custom", "1.0.0")
