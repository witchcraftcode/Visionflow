import onnxruntime as ort
import numpy as np
from pathlib import Path


class ResNet18Model:
    def __init__(self, providers: list[str] | None = None):
        model_path = Path(__file__).parent / "onnx" / "resnet18.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, image):
        return self.predict_batch([image])[0]

    def predict_batch(self, images):
        batch = np.stack([np.transpose(image, (2, 0, 1)) for image in images], axis=0)
        outputs = self.session.run(None, {self.input_name: batch})
        probs_batch = outputs[0]
        return [
            {
                "label": int(np.argmax(probs)),
                "confidence": float(np.max(probs)),
            }
            for probs in probs_batch
        ]

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
        return "resnet18"
