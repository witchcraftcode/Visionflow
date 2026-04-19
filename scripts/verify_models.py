import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TEST_IMAGE = ROOT_DIR / "test.jpg"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import load_model_config
from app.models.adapter import VisionModelAdapter
from app.models.registry import get_model, list_models


def main():
    image_bytes = TEST_IMAGE.read_bytes()

    for model_name in list_models():
        model = get_model(model_name)
        config = load_model_config(model_name)
        result = VisionModelAdapter(model=model, config=config).predict(image_bytes)
        if not isinstance(result, dict) or not result:
            raise RuntimeError(f"Model '{model_name}' returned an invalid prediction payload: {result!r}")
        print(f"verified {model_name}: {result}")


if __name__ == "__main__":
    main()
