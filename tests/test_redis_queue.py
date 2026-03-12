from app.queue import redis_queue


class FakeRedis:
    def __init__(self):
        self.counts = {}
        self.expirations = {}

    def time(self):
        return (120, 0)

    def incr(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key, seconds):
        self.expirations[key] = seconds


def test_consume_rate_limit(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(redis_queue, "redis_client", fake)

    assert redis_queue.consume_rate_limit("client-a", 2, 60) is True
    assert redis_queue.consume_rate_limit("client-a", 2, 60) is True
    assert redis_queue.consume_rate_limit("client-a", 2, 60) is False

    assert list(fake.expirations.values()) == [60]
