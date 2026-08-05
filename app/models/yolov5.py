import onnxruntime as ort
import numpy as np
from pathlib import Path


class YOLOv5Model:
    def __init__(self, providers: list[str] | None = None):
        model_path = Path(__file__).parent / "onnx" / "yolov5n.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    def _parse_outputs(self, outputs):
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

    def predict(self, image):
        return self.predict_batch([image])[0]

    def predict_batch(self, images):
        batch = np.stack([np.transpose(image, (2, 0, 1)) for image in images], axis=0)
        outputs = self.session.run(None, {self.input_name: batch})[0]
        if outputs.ndim == 3 and outputs.shape[1] <= 128 and outputs.shape[1] != outputs.shape[2]:
            outputs = outputs.transpose(0, 2, 1)
        return [self._parse_outputs(sample) for sample in outputs]

    @property
    def available_providers(self):
        return self.session.get_providers()

    @property
    def runtime_name(self):
        return "onnx"

    @property
    def execution_provider(self):
        return self.available_providers[0] if self.available_providers else "unknown"

    def supports_batch_inference(self):
        return True

    def supports_gpu(self):
        return any(provider.startswith("CUDA") for provider in self.available_providers)

    def provider_label(self):
        return self.execution_provider

    def comparison_family(self):
        return "yolov5"
