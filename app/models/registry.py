import importlib

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

_MODEL_CACHE = {}


def get_model(model_name: str, version: str | None = None):
    resolved = resolve_model_version(model_name, version)
    cache_key = f"{model_name}:{resolved}"

    if cache_key not in _MODEL_CACHE:
        print(f"[registry] loading model: {cache_key}", flush=True)
        class_path = model_metadata(model_name, resolved)["class"]
        module_name, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        model_cls = getattr(module, class_name)
        _MODEL_CACHE[cache_key] = model_cls()

    return _MODEL_CACHE[cache_key]
