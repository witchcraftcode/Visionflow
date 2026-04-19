import numpy as np
import pytest

from app.models.yolov5 import YOLOv5Model


def test_yolov5_predict_handles_channel_first_output():
    model = YOLOv5Model.__new__(YOLOv5Model)

    class FakeSession:
        def run(self, _, __):
            output = np.zeros((1, 84, 2), dtype=np.float32)
            output[0, :4, 0] = [10.0, 20.0, 30.0, 40.0]
            output[0, 4 + 3, 0] = 0.91
            output[0, :4, 1] = [1.0, 2.0, 3.0, 4.0]
            output[0, 4 + 1, 1] = 0.12
            return [output]

    model.session = FakeSession()
    model.input_name = "images"

    image = np.zeros((640, 640, 3), dtype=np.float32)
    result = model.predict(image)

    assert len(result["detections"]) == 1
    assert result["detections"][0]["bbox"] == [10.0, 20.0, 30.0, 40.0]
    assert result["detections"][0]["class"] == 3
    assert result["detections"][0]["confidence"] == pytest.approx(0.91)
