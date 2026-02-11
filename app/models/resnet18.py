import onnxruntime as ort
import numpy as np
from pathlib import Path

class ResNet18Model:
    def __init__(self):
        model_path = Path(__file__).parent / "onnx" / "resnet18.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")
        self.session = ort.InferenceSession(str(model_path))
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, image):
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, 0)
        outputs = self.session.run(None, {self.input_name: image})
        probs = outputs[0][0]

        return {
            "label": int(np.argmax(probs)),
            "confidence": float(np.max(probs))
        }
