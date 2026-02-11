from app.preprocessing.image import preprocess_image


class VisionModelAdapter:
    def __init__(self, model, config: dict):
        self.model = model
        self.config = config

    def predict(self, image_bytes: bytes):
        # Step 1: preprocess according to model config
        image_array = preprocess_image(image_bytes, self.config)

        # Step 2: run model inference
        result = self.model.predict(image_array)

        return result
