import importlib

_MODEL_IMPORTS = {
    "resnet18": ("app.models.resnet18", "ResNet18Model"),
    "mobilenet": ("app.models.mobilenet", "MobileNetV2Model"),
    "yolov5": ("app.models.yolov5", "YOLOv5Model"),
}

_MODEL_CACHE = {}

def list_models():
    return sorted(_MODEL_IMPORTS.keys())

def has_model(model_name: str) -> bool:
    return model_name in _MODEL_IMPORTS

def get_model(model_name: str):
    if model_name not in _MODEL_IMPORTS:
        raise ValueError(f"Unknown model '{model_name}'")

    if model_name not in _MODEL_CACHE:
        print(f"[registry] loading model: {model_name}", flush=True)
        module_name, class_name = _MODEL_IMPORTS[model_name]
        module = importlib.import_module(module_name)
        model_cls = getattr(module, class_name)
        _MODEL_CACHE[model_name] = model_cls()

    return _MODEL_CACHE[model_name]
