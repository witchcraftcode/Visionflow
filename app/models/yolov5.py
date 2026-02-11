import onnxruntime as ort
import numpy as np
from pathlib import Path

class YOLOv5Model:
    def __init__(self):
        model_path = Path(__file__).parent / "onnx" / "yolov5n.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")
        self.session = ort.InferenceSession(str(model_path))
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, image):
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, 0)

        outputs = self.session.run(None, {self.input_name: image})[0]

        detections = []
        for det in outputs:
            if det[4] > 0.4:
                detections.append({
                    "bbox": det[:4].tolist(),
                    "confidence": float(det[4]),
                    "class": int(det[5])
                })

        return {"detections": detections}
