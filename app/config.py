import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "configs" / "models"

def load_model_config(model_name: str):
    path = CONFIG_DIR / f"{model_name}.json"
    if not path.exists():
        raise ValueError(f"No config for model '{model_name}'")

    with open(path) as f:
        return json.load(f)
