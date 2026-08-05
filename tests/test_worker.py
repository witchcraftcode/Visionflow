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
    monkeypatch.setattr(worker_mod, "track_queue_wait", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker_mod, "track_model_inference", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker_mod, "set_worker_utilization", lambda **kwargs: None)
    monkeypatch.setattr(
        worker_mod,
        "psutil",
        type(
            "FakePsutil",
            (),
            {
                "cpu_percent": staticmethod(lambda interval=None: 10.0),
                "virtual_memory": staticmethod(lambda: type("VM", (), {"percent": 20.0})()),
            },
        )(),
    )

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
    monkeypatch.setattr(worker_mod, "track_queue_wait", lambda *args, **kwargs: None)

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
    monkeypatch.setattr(worker_mod, "track_queue_wait", lambda *args, **kwargs: None)

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


def test_recover_stale_jobs_requeues_processing_job(monkeypatch):
    now = 1_000.0
    store = {
        "job-stale": {
            "job_id": "job-stale",
            "status": "processing",
            "model": "resnet18",
            "model_version": "1.0.0",
            "started_at": now - 200,
            "timeout_seconds": 60,
            "attempt": 0,
            "max_retries": 3,
        }
    }
    requeued = []

    monkeypatch.setattr(worker_mod, "_now", lambda: now)
    monkeypatch.setattr(worker_mod, "iter_jobs", lambda: iter(store.items()))
    monkeypatch.setattr(worker_mod, "set_job", lambda jid, data: store.__setitem__(jid, data))
    monkeypatch.setattr(worker_mod, "enqueue_job", lambda jid: requeued.append(jid))
    monkeypatch.setattr(worker_mod, "set_worker_health", lambda **kwargs: None)

    recovered, stale_detected = worker_mod.recover_stale_jobs()

    assert recovered == 1
    assert stale_detected == 1
    assert store["job-stale"]["status"] == "queued"
    assert store["job-stale"]["started_at"] is None
    assert requeued == ["job-stale"]


def test_worker_processes_batch_job(monkeypatch):
    store = {}
    job_id = "job-batch"

    monkeypatch.setattr(worker_mod, "dequeue_job", lambda: job_id)
    monkeypatch.setattr(worker_mod, "get_job", lambda jid: store.get(jid))
    monkeypatch.setattr(worker_mod, "set_job", lambda jid, data: store.__setitem__(jid, data))
    monkeypatch.setattr(worker_mod, "get_model", lambda name, version=None: DummyModel())
    monkeypatch.setattr(worker_mod, "load_model_config", lambda name: {"input_size": [224, 224], "color_mode": "RGB"})
    monkeypatch.setattr(worker_mod, "track_queue_wait", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker_mod, "track_model_inference", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker_mod, "set_worker_utilization", lambda **kwargs: None)
    monkeypatch.setattr(worker_mod, "psutil", None)

    def fake_predict_batch(self, image_bytes_list):
        return [{"label": index, "confidence": 0.9} for index, _ in enumerate(image_bytes_list)]

    monkeypatch.setattr(worker_mod.VisionModelAdapter, "predict_batch", fake_predict_batch)

    store[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "model": "resnet18",
        "model_version": "1.0.0",
        "image_bytes_list": ["00", "01"],
        "result": None,
        "error": None,
    }

    worker_mod.process_one_job()

    assert store[job_id]["status"] == "completed"
    assert store[job_id]["result"][1]["label"] == 1


def test_worker_resets_started_at_for_requeued_stale_job(monkeypatch):
    store = {}
    job_id = "job-recovered"
    stale_started_at = 100.0
    now = 1_000.0

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
        "job_id": job_id,
        "status": "queued",
        "model": "resnet18",
        "model_version": "1.0.0",
        "image_bytes": "00",
        "result": None,
        "error": None,
        "attempt": 1,
        "max_retries": 3,
        "timeout_seconds": 60,
        "started_at": stale_started_at,
    }

    monkeypatch.setattr(worker_mod, "_now", lambda: now)
    monkeypatch.setattr(worker_mod, "dequeue_job", dequeue_job)
    monkeypatch.setattr(worker_mod, "get_job", get_job)
    monkeypatch.setattr(worker_mod, "set_job", set_job)
    monkeypatch.setattr(worker_mod, "get_model", get_model)
    monkeypatch.setattr(worker_mod, "load_model_config", load_model_config)
    monkeypatch.setattr(worker_mod.VisionModelAdapter, "predict", fake_predict)
    monkeypatch.setattr(worker_mod, "track_queue_wait", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker_mod, "track_model_inference", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker_mod, "psutil", None)

    worker_mod.process_one_job()

    assert store[job_id]["status"] == "completed"
    assert store[job_id]["started_at"] == now
    assert store[job_id]["duration_ms"] == 0
