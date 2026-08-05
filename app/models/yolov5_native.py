from pathlib import Path

import numpy as np


class NativeYOLOv5Model:
    def __init__(self, device: str = "cpu"):
        try:
            from ultralytics import YOLO
        except ImportError as exc:  # pragma: no cover - optional benchmark runtime
            raise RuntimeError("Native YOLO runtime requires the 'ultralytics' package") from exc

        self.device = device
        model_path = Path(__file__).parent / "onnx" / "yolov5nu.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")
        self.model = YOLO(str(model_path))
        self.model.to(device)

    def _to_detection_result(self, result):
        detections = []
        boxes = result.boxes
        if boxes is None:
            return {"detections": detections}
        xyxy = boxes.xyxy.detach().cpu().numpy()
        conf = boxes.conf.detach().cpu().numpy()
        cls = boxes.cls.detach().cpu().numpy()
        for bbox, confidence, class_id in zip(xyxy, conf, cls, strict=False):
            detections.append(
                {
                    "bbox": [float(value) for value in bbox.tolist()],
                    "confidence": float(confidence),
                    "class": int(class_id),
                }
            )
        return {"detections": detections}

    def predict(self, image):
        return self.predict_batch([image])[0]

    def predict_batch(self, images):
        arrays = [np.clip(image * 255.0 if image.max() <= 1.0 else image, 0, 255).astype(np.uint8) for image in images]
        results = self.model.predict(arrays, device=self.device, verbose=False)
        return [self._to_detection_result(result) for result in results]

    @property
    def runtime_name(self):
        return "native"

    @property
    def execution_provider(self):
        return self.device

    def supports_batch_inference(self):
        return True

    def supports_gpu(self):
        return self.device == "cuda"

    def provider_label(self):
        return self.device

    def comparison_family(self):
        return "yolov5"
