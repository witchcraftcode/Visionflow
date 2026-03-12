import importlib
import json
from pathlib import Path
from threading import Lock

REGISTRY_PATH = Path(__file__).parent.parent / "configs" / "model_registry.json"
_LOCK = Lock()


def _load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)["models"]


def _save_registry(models: dict):
    with open(REGISTRY_PATH, "w") as f:
        json.dump({"models": models}, f, indent=2)


_MODELS = _load_registry()

_MODEL_CACHE = {}

def list_models():
    return sorted(_MODELS.keys())

def has_model(model_name: str, version: str | None = None) -> bool:
    if model_name not in _MODELS:
        return False
    if version is None:
        return True
    return version in _MODELS[model_name]["versions"]


def list_model_versions(model_name: str):
    if model_name not in _MODELS:
        raise ValueError(f"Unknown model '{model_name}'")
    return sorted(_MODELS[model_name]["versions"].keys())


def resolve_model_version(model_name: str, version: str | None):
    if model_name not in _MODELS:
        raise ValueError(f"Unknown model '{model_name}'")
    if version is None:
        return _MODELS[model_name]["default_version"]
    if version not in _MODELS[model_name]["versions"]:
        raise ValueError(f"Unknown version '{version}' for model '{model_name}'")
    return version


def model_metadata(model_name: str, version: str | None = None):
    resolved = resolve_model_version(model_name, version)
    model = _MODELS[model_name]
    payload = model["versions"][resolved].copy()
    payload["name"] = model_name
    payload["version"] = resolved
    payload["default_version"] = model["default_version"]
    return payload


def register_model_version(model_name: str, version: str, payload: dict):
    with _LOCK:
        models = _load_registry()
        if model_name not in models:
            models[model_name] = {
                "default_version": version,
                "versions": {},
            }
        versions = models[model_name]["versions"]
        if version in versions:
            raise ValueError(f"Version '{version}' already exists for model '{model_name}'")
        versions[version] = payload
        _save_registry(models)
        _MODELS.clear()
        _MODELS.update(models)


def promote_model_version(model_name: str, version: str):
    with _LOCK:
        models = _load_registry()
        if model_name not in models or version not in models[model_name]["versions"]:
            raise ValueError(f"Unknown model/version '{model_name}:{version}'")
        models[model_name]["default_version"] = version
        _save_registry(models)
        _MODELS.clear()
        _MODELS.update(models)


def get_model(model_name: str, version: str | None = None):
    resolved = resolve_model_version(model_name, version)
    cache_key = f"{model_name}:{resolved}"

    if cache_key not in _MODEL_CACHE:
        print(f"[registry] loading model: {cache_key}", flush=True)
        class_path = _MODELS[model_name]["versions"][resolved]["class"]
        module_name, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        model_cls = getattr(module, class_name)
        _MODEL_CACHE[cache_key] = model_cls()

    return _MODEL_CACHE[cache_key]
