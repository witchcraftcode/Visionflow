import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

QUEUE_NAME = "queue:jobs"


def enqueue_job(job_id: str):
    print("[enqueue_job] pushing:", job_id)
    redis_client.rpush(QUEUE_NAME, job_id)


def dequeue_job():
    _, job_id = redis_client.blpop(QUEUE_NAME)
    print("[dequeue_job] popped:", job_id)
    return job_id


def set_job(job_id: str, data: dict):
    redis_client.set(f"job:{job_id}", json.dumps(data))


def get_job(job_id: str):
    data = redis_client.get(f"job:{job_id}")
    if data is None:
        return None
    return json.loads(data)
