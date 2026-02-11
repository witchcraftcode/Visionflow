from app import worker as worker_mod


class DummyModel:
    def predict(self, image):
        return {"label": 1, "confidence": 0.5}


def test_worker_process_one_job(monkeypatch):
    store = {}
    job_id = "job-123"

    def dequeue_job():
        return job_id

    def get_job(jid):
        return store.get(jid)

    def set_job(jid, data):
        store[jid] = data

    def get_model(name):
        return DummyModel()

    def load_model_config(name):
        return {"input_size": [224, 224], "color_mode": "RGB"}

    def fake_predict(self, image_bytes):
        return {"label": 7, "confidence": 0.9}

    store[job_id] = {
        "status": "queued",
        "model": "resnet18",
        "image_bytes": "00",
        "result": None,
        "error": None,
    }

    monkeypatch.setattr(worker_mod, "dequeue_job", dequeue_job)
    monkeypatch.setattr(worker_mod, "get_job", get_job)
    monkeypatch.setattr(worker_mod, "set_job", set_job)
    monkeypatch.setattr(worker_mod, "get_model", get_model)
    monkeypatch.setattr(worker_mod, "load_model_config", load_model_config)
    monkeypatch.setattr(worker_mod.VisionModelAdapter, "predict", fake_predict)

    worker_mod.process_one_job()

    assert store[job_id]["status"] == "completed"
    assert store[job_id]["result"]["label"] == 7
