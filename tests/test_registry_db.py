from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services import registry_db


def configure_temp_registry(monkeypatch, tmp_path):
    database_url = f"sqlite:///{tmp_path / 'registry.db'}"
    engine = create_engine(database_url, future=True, connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(registry_db, "engine", engine)
    monkeypatch.setattr(registry_db, "SessionLocal", session_local)
    monkeypatch.setattr(registry_db, "_INITIALIZED", True)
    Base.metadata.create_all(bind=engine)
    return engine


def test_registry_db_crud(monkeypatch, tmp_path):
    engine = configure_temp_registry(monkeypatch, tmp_path)
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())

    payload = {
        "runtime": "onnx",
        "artifact_uri": "app/models/onnx/custom.onnx",
        "class": "app.models.onnx_model.ONNXVisionModel",
        "input_schema": {"type": "image"},
        "output_schema": {"type": "classification"},
        "resources": {"cpu": "500m", "memory": "512Mi"},
    }

    registry_db.register_model_version("custom", "1.0.0", payload)
    assert registry_db.list_models() == ["custom"]
    assert registry_db.resolve_model_version("custom", None) == "1.0.0"

    registry_db.update_model_version("custom", "1.0.0", {"artifact_uri": "s3://later/custom.onnx"})
    assert registry_db.model_metadata("custom", "1.0.0")["artifact_uri"] == "s3://later/custom.onnx"

    registry_db.register_model_version("custom", "1.1.0", payload)
    registry_db.promote_model_version("custom", "1.1.0")
    assert registry_db.resolve_model_version("custom", None) == "1.1.0"

    registry_db.delete_model_version("custom", "1.1.0")
    assert registry_db.resolve_model_version("custom", None) == "1.0.0"
