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
        if outputs.ndim == 3 and outputs.shape[0] == 1:
            outputs = outputs[0]
        if outputs.ndim == 2 and outputs.shape[0] <= 128 and outputs.shape[0] != outputs.shape[1]:
            outputs = outputs.transpose(1, 0)

        detections = []
        for det in outputs:
            if len(det) <= 5:
                continue
            class_scores = det[4:]
            confidence = float(np.max(class_scores))
            if confidence > 0.4:
                detections.append({
                    "bbox": det[:4].tolist(),
                    "confidence": confidence,
                    "class": int(np.argmax(class_scores)),
                })

        return {"detections": detections}
