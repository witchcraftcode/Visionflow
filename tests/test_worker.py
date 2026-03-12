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

    def get_model(name, version=None):
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


def test_worker_retries_then_requeues(monkeypatch):
    store = {}
    job_id = "job-retry"
    requeued = []

    def dequeue_job():
        return job_id

    def get_job(jid):
        return store.get(jid)

    def set_job(jid, data):
        store[jid] = data

    def get_model(name, version=None):
        return DummyModel()

    def load_model_config(name):
        return {"input_size": [224, 224], "color_mode": "RGB"}

    def fake_predict(self, image_bytes):
        raise RuntimeError("transient failure")

    monkeypatch.setattr(worker_mod, "dequeue_job", dequeue_job)
    monkeypatch.setattr(worker_mod, "get_job", get_job)
    monkeypatch.setattr(worker_mod, "set_job", set_job)
    monkeypatch.setattr(worker_mod, "get_model", get_model)
    monkeypatch.setattr(worker_mod, "load_model_config", load_model_config)
    monkeypatch.setattr(worker_mod.VisionModelAdapter, "predict", fake_predict)
    monkeypatch.setattr(worker_mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(worker_mod, "enqueue_job", lambda jid: requeued.append(jid))

    store[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "model": "resnet18",
        "model_version": "1.0.0",
        "image_bytes": "00",
        "result": None,
        "error": None,
        "attempt": 0,
        "max_retries": 3,
    }

    worker_mod.process_one_job()

    assert store[job_id]["status"] == "queued"
    assert store[job_id]["attempt"] == 1
    assert requeued == [job_id]


def test_worker_dead_letters_after_exhausted_retries(monkeypatch):
    store = {}
    job_id = "job-dlq"
    dead_letter = []

    def dequeue_job():
        return job_id

    def get_job(jid):
        return store.get(jid)

    def set_job(jid, data):
        store[jid] = data

    def get_model(name, version=None):
        return DummyModel()

    def load_model_config(name):
        return {"input_size": [224, 224], "color_mode": "RGB"}

    def fake_predict(self, image_bytes):
        raise RuntimeError("permanent failure")

    monkeypatch.setattr(worker_mod, "dequeue_job", dequeue_job)
    monkeypatch.setattr(worker_mod, "get_job", get_job)
    monkeypatch.setattr(worker_mod, "set_job", set_job)
    monkeypatch.setattr(worker_mod, "get_model", get_model)
    monkeypatch.setattr(worker_mod, "load_model_config", load_model_config)
    monkeypatch.setattr(worker_mod.VisionModelAdapter, "predict", fake_predict)
    monkeypatch.setattr(worker_mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(worker_mod, "enqueue_dead_letter", lambda jid: dead_letter.append(jid))

    store[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "model": "resnet18",
        "model_version": "1.0.0",
        "image_bytes": "00",
        "result": None,
        "error": None,
        "attempt": 3,
        "max_retries": 3,
    }

    worker_mod.process_one_job()

    assert store[job_id]["status"] == "dead_lettered"
    assert dead_letter == [job_id]
