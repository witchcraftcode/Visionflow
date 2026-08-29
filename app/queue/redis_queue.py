import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", 86400))
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", 3600))
RATE_LIMIT_PREFIX = "ratelimit"

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_timeout=None,           
    socket_connect_timeout=5,
)


QUEUE_NAME = "visionflow:jobs"
DLQ_NAME = "queue:jobs:dlq"


def enqueue_job(job_id: str):
    print("[enqueue_job] pushing:", job_id)
    redis_client.rpush(QUEUE_NAME, job_id)


def enqueue_dead_letter(job_id: str):
    print("[enqueue_dead_letter] pushing:", job_id)
    redis_client.rpush(DLQ_NAME, job_id)




def dequeue_job():
    item = redis_client.blpop(QUEUE_NAME, timeout=5)

    if item is None:
        return None

    _, job_id = item

    # Works for both bytes and str
    if isinstance(job_id, bytes):
        return job_id.decode("utf-8")

    return job_id


def set_job(job_id: str, data: dict):
    redis_client.set(f"job:{job_id}", json.dumps(data), ex=JOB_TTL_SECONDS)


def get_job(job_id: str):
    data = redis_client.get(f"job:{job_id}")
    if data is None:
        return None
    return json.loads(data)


def iter_jobs():
    for key in redis_client.scan_iter(match="job:*"):
        job_id = key.split("job:", 1)[1]
        job = get_job(job_id)
        if job is not None:
            yield job_id, job


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


def consume_rate_limit(client_id: str, limit: int, window_seconds: int) -> bool:
    window_start = int(redis_client.time()[0] // window_seconds) * window_seconds
    key = f"{RATE_LIMIT_PREFIX}:{client_id}:{window_start}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window_seconds)
    return int(current) <= limit
