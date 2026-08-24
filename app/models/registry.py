import importlib
import inspect

from app.services.registry_db import (
    delete_model_version,
    has_model,
    list_model_versions,
    list_models,
    model_metadata,
    promote_model_version,
    register_model_version,
    resolve_model_version,
    update_model_version,
)
from app.storage.artifacts import artifact_manager

_MODEL_CACHE = {}


def get_model(model_name: str, version: str | None = None):
    resolved = resolve_model_version(model_name, version)
    cache_key = f"{model_name}:{resolved}"

    if cache_key not in _MODEL_CACHE:
        print(f"[registry] loading model: {cache_key}", flush=True)
        metadata = model_metadata(model_name, resolved)
        class_path = metadata["class"]
        artifact_path = artifact_manager.resolve(
            metadata["artifact_uri"],
            expected_sha256=metadata.get("artifact_sha256"),
        )
        module_name, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        model_cls = getattr(module, class_name)
        signature = inspect.signature(model_cls)
        if "model_path" in signature.parameters:
            _MODEL_CACHE[cache_key] = model_cls(model_path=str(artifact_path))
        else:
            _MODEL_CACHE[cache_key] = model_cls()

    return _MODEL_CACHE[cache_key]
