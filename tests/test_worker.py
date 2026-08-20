from app import worker as worker_mod
from app.services.queue import QueueService


class InMemoryQueueBackend:
    def __init__(self, store=None, enqueued=None):
        self.store = {} if store is None else store
        self.enqueued = [] if enqueued is None else enqueued
        self.dead_lettered = []
        self.idempotency = {}

    def enqueue_job(self, job_id: str):
        self.enqueued.append(job_id)

    def enqueue_dead_letter(self, job_id: str):
        self.dead_lettered.append(job_id)

    def dequeue_job(self):
        return self.enqueued.pop(0)

    def set_job(self, job_id: str, data: dict):
        self.store[job_id] = data

    def get_job(self, job_id: str):
        return self.store.get(job_id)

    def iter_jobs(self):
        return iter(self.store.items())

    def set_idempotency_job(self, key: str, job_id: str):
        self.idempotency[key] = job_id

    def get_idempotency_job(self, key: str):
        return self.idempotency.get(key)

    def queue_depth(self) -> int:
        return len(self.enqueued)

    def dead_letter_depth(self) -> int:
        return len(self.dead_lettered)

    def ping(self) -> bool:
        return True


def use_memory_queue(monkeypatch, store, enqueued):
    backend = InMemoryQueueBackend(store=store, enqueued=enqueued)
    monkeypatch.setattr(worker_mod, "queue_service", QueueService(backend))
    return backend


class DummyModel:
    def predict(self, image):
        return {"label": 1, "confidence": 0.5}


def test_worker_process_one_job(monkeypatch):
    store = {}
    job_id = "job-123"

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

    use_memory_queue(monkeypatch, store=store, enqueued=[job_id])
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

    def get_model(name, version=None):
        return DummyModel()

    def load_model_config(name):
        return {"input_size": [224, 224], "color_mode": "RGB"}

    def fake_predict(self, image_bytes):
        raise RuntimeError("transient failure")

    backend = use_memory_queue(monkeypatch, store=store, enqueued=[job_id])
    monkeypatch.setattr(worker_mod, "get_model", get_model)
    monkeypatch.setattr(worker_mod, "load_model_config", load_model_config)
    monkeypatch.setattr(worker_mod.VisionModelAdapter, "predict", fake_predict)
    monkeypatch.setattr(worker_mod.time, "sleep", lambda s: None)
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
    assert backend.enqueued == [job_id]


def test_worker_dead_letters_after_exhausted_retries(monkeypatch):
    store = {}
    job_id = "job-dlq"

    def get_model(name, version=None):
        return DummyModel()

    def load_model_config(name):
        return {"input_size": [224, 224], "color_mode": "RGB"}

    def fake_predict(self, image_bytes):
        raise RuntimeError("permanent failure")

    backend = use_memory_queue(monkeypatch, store=store, enqueued=[job_id])
    monkeypatch.setattr(worker_mod, "get_model", get_model)
    monkeypatch.setattr(worker_mod, "load_model_config", load_model_config)
    monkeypatch.setattr(worker_mod.VisionModelAdapter, "predict", fake_predict)
    monkeypatch.setattr(worker_mod.time, "sleep", lambda s: None)
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
    assert backend.dead_lettered == [job_id]


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
    backend = use_memory_queue(monkeypatch, store=store, enqueued=requeued)
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

    use_memory_queue(monkeypatch, store=store, enqueued=[job_id])
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
    use_memory_queue(monkeypatch, store=store, enqueued=[job_id])
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
