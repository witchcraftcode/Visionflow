import onnxruntime as ort
import numpy as np

class ONNXVisionModel:
    def __init__(self, model_path: str):
        if not model_path:
            raise ValueError("model_path is required")
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, image_array: np.ndarray):
        """
        image_array: (H, W, C) numpy array
        """
        # Convert to NCHW + batch
        image = image_array.astype(np.float32)
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, axis=0)

        outputs = self.session.run(None, {
            self.input_name: image
        })

        logits = outputs[0][0]
        label = int(np.argmax(logits))
        confidence = float(np.max(logits))

        return {
            "label": label,
            "confidence": confidence
        }
