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

    def predict_batch(self, image_bytes_list: list[bytes]):
        image_arrays = [preprocess_image(image_bytes, self.config) for image_bytes in image_bytes_list]
        if hasattr(self.model, "predict_batch"):
            return self.model.predict_batch(image_arrays)
        return [self.model.predict(image_array) for image_array in image_arrays]
