import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", 86400))
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", 3600))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

QUEUE_NAME = "queue:jobs"
DLQ_NAME = "queue:jobs:dlq"


def enqueue_job(job_id: str):
    print("[enqueue_job] pushing:", job_id)
    redis_client.rpush(QUEUE_NAME, job_id)


def enqueue_dead_letter(job_id: str):
    print("[enqueue_dead_letter] pushing:", job_id)
    redis_client.rpush(DLQ_NAME, job_id)


def dequeue_job():
    _, job_id = redis_client.blpop(QUEUE_NAME)
    print("[dequeue_job] popped:", job_id)
    return job_id


def set_job(job_id: str, data: dict):
    redis_client.set(f"job:{job_id}", json.dumps(data), ex=JOB_TTL_SECONDS)


def get_job(job_id: str):
    data = redis_client.get(f"job:{job_id}")
    if data is None:
        return None
    return json.loads(data)


def set_idempotency_job(key: str, job_id: str):
    redis_client.set(f"idempotency:{key}", job_id, ex=IDEMPOTENCY_TTL_SECONDS)


def get_idempotency_job(key: str):
    return redis_client.get(f"idempotency:{key}")


def queue_depth() -> int:
    return int(redis_client.llen(QUEUE_NAME))


def dead_letter_depth() -> int:
    return int(redis_client.llen(DLQ_NAME))


def ping() -> bool:
    return bool(redis_client.ping())
