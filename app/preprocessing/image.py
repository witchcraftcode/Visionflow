from fastapi import HTTPException
from PIL import Image
import numpy as np
import io


def preprocess_image(image_bytes: bytes, config: dict) -> np.ndarray:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert(config["color_mode"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    image = image.resize(tuple(config["input_size"]))
    image_array = np.array(image).astype(np.float32)

    norm = config.get("normalization", {})
    if norm.get("type") == "scale":
        image_array = image_array / np.float32(norm.get("value", 255.0))

    return image_array
