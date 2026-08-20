import json
from pathlib import Path
from threading import RLock

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.models import ModelVersion, RegisteredModel
from app.db.session import SessionLocal, engine, is_sqlite

REGISTRY_SEED_PATH = Path(__file__).resolve().parents[1] / "configs" / "model_registry.json"
_LOCK = RLock()
_INITIALIZED = False


def _model_version_payload(version: ModelVersion, model: RegisteredModel) -> dict:
    return {
        "runtime": version.runtime,
        "artifact_uri": version.artifact_uri,
        "class": version.class_path,
        "input_schema": version.input_schema,
        "output_schema": version.output_schema,
        "resources": version.resources,
        "name": model.name,
        "version": version.version,
        "default_version": model.default_version,
    }


def _load_seed_models():
    with open(REGISTRY_SEED_PATH) as f:
        return json.load(f)["models"]


def initialize_registry_store():
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _LOCK:
        if _INITIALIZED:
            return
        if is_sqlite() and settings.auto_create_sqlite_schema:
            Base.metadata.create_all(bind=engine)
        with SessionLocal() as session:
            has_models = session.scalar(select(RegisteredModel.id).limit(1)) is not None
            if not has_models:
                seed_registry(session)
                session.commit()
        _INITIALIZED = True


def seed_registry(session: Session):
    for model_name, model_payload in _load_seed_models().items():
        model = RegisteredModel(name=model_name, default_version=model_payload.get("default_version"))
        session.add(model)
        session.flush()
        for version, version_payload in model_payload.get("versions", {}).items():
            session.add(
                ModelVersion(
                    model_id=model.id,
                    version=version,
                    runtime=version_payload["runtime"],
                    artifact_uri=version_payload["artifact_uri"],
                    class_path=version_payload["class"],
                    input_schema=version_payload.get("input_schema", {}),
                    output_schema=version_payload.get("output_schema", {}),
                    resources=version_payload.get("resources", {}),
                    is_active=True,
                )
            )


def _session():
    initialize_registry_store()
    return SessionLocal()


def _get_model(session: Session, model_name: str) -> RegisteredModel | None:
    return session.scalar(select(RegisteredModel).where(RegisteredModel.name == model_name))


def _get_version(session: Session, model_name: str, version: str) -> tuple[RegisteredModel, ModelVersion] | None:
    stmt = (
        select(RegisteredModel, ModelVersion)
        .join(ModelVersion, ModelVersion.model_id == RegisteredModel.id)
        .where(RegisteredModel.name == model_name, ModelVersion.version == version)
    )
    row = session.execute(stmt).first()
    if row is None:
        return None
    return row[0], row[1]


def list_models():
    with _session() as session:
        return list(session.scalars(select(RegisteredModel.name).order_by(RegisteredModel.name)))


def has_model(model_name: str, version: str | None = None) -> bool:
    with _session() as session:
        if version is None:
            return _get_model(session, model_name) is not None
        return _get_version(session, model_name, version) is not None


def list_model_versions(model_name: str):
    with _session() as session:
        model = _get_model(session, model_name)
        if model is None:
            raise ValueError(f"Unknown model '{model_name}'")
        return list(
            session.scalars(
                select(ModelVersion.version)
                .where(ModelVersion.model_id == model.id)
                .order_by(ModelVersion.version)
            )
        )


def resolve_model_version(model_name: str, version: str | None):
    with _session() as session:
        model = _get_model(session, model_name)
        if model is None:
            raise ValueError(f"Unknown model '{model_name}'")
        if version is None:
            return model.default_version
        if _get_version(session, model_name, version) is None:
            raise ValueError(f"Unknown version '{version}' for model '{model_name}'")
        return version


def model_metadata(model_name: str, version: str | None = None):
    with _session() as session:
        resolved = resolve_model_version(model_name, version)
        row = _get_version(session, model_name, resolved)
        if row is None:
            raise ValueError(f"Unknown model/version '{model_name}:{resolved}'")
        model, model_version = row
        return _model_version_payload(model_version, model)


def register_model_version(model_name: str, version: str, payload: dict):
    with _LOCK:
        with _session() as session:
            model = _get_model(session, model_name)
            if model is None:
                model = RegisteredModel(name=model_name, default_version=version)
                session.add(model)
                session.flush()
            elif _get_version(session, model_name, version) is not None:
                raise ValueError(f"Version '{version}' already exists for model '{model_name}'")

            session.add(
                ModelVersion(
                    model_id=model.id,
                    version=version,
                    runtime=payload["runtime"],
                    artifact_uri=payload["artifact_uri"],
                    class_path=payload["class"],
                    input_schema=payload.get("input_schema", {}),
                    output_schema=payload.get("output_schema", {}),
                    resources=payload.get("resources", {}),
                    is_active=True,
                )
            )
            if model.default_version is None:
                model.default_version = version
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValueError(f"Version '{version}' already exists for model '{model_name}'") from exc


def update_model_version(model_name: str, version: str, payload: dict):
    with _LOCK:
        with _session() as session:
            row = _get_version(session, model_name, version)
            if row is None:
                raise ValueError(f"Unknown model/version '{model_name}:{version}'")
            _, model_version = row
            for source_key, attr in {
                "runtime": "runtime",
                "artifact_uri": "artifact_uri",
                "class": "class_path",
                "input_schema": "input_schema",
                "output_schema": "output_schema",
                "resources": "resources",
            }.items():
                if source_key in payload and payload[source_key] is not None:
                    setattr(model_version, attr, payload[source_key])
            session.commit()


def delete_model_version(model_name: str, version: str):
    with _LOCK:
        with _session() as session:
            row = _get_version(session, model_name, version)
            if row is None:
                raise ValueError(f"Unknown model/version '{model_name}:{version}'")
            model, model_version = row
            if model.default_version == version:
                other_version = session.scalar(
                    select(ModelVersion.version)
                    .where(ModelVersion.model_id == model.id, ModelVersion.version != version)
                    .order_by(ModelVersion.version)
                    .limit(1)
                )
                model.default_version = other_version
            session.delete(model_version)
            session.flush()
            if model.default_version is None:
                session.delete(model)
            session.commit()


def promote_model_version(model_name: str, version: str):
    with _LOCK:
        with _session() as session:
            row = _get_version(session, model_name, version)
            if row is None:
                raise ValueError(f"Unknown model/version '{model_name}:{version}'")
            model, _ = row
            model.default_version = version
            session.commit()
