from app import audit


class FakeRedis:
    def __init__(self):
        self.values = {}

    def lpush(self, key, value):
        self.values.setdefault(key, [])
        self.values[key].insert(0, value)

    def ltrim(self, key, start, end):
        self.values[key] = self.values.get(key, [])[start : end + 1]

    def lrange(self, key, start, end):
        return self.values.get(key, [])[start : end + 1]


def test_record_and_list_admin_audit_events(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(audit, "redis_client", fake)
    monkeypatch.setattr(audit, "AUDIT_LOG_LIMIT", 2)

    audit.record_admin_audit_event("model_registered", model="resnet18", version="1.0.0")
    audit.record_admin_audit_event("model_promoted", model="resnet18", version="1.0.1")
    audit.record_admin_audit_event("model_registered", model="mobilenet", version="1.0.0")

    events = audit.list_admin_audit_events(limit=10)
    assert len(events) == 2
    assert events[0]["action"] == "model_registered"
    assert events[0]["model"] == "mobilenet"
    assert events[1]["action"] == "model_promoted"
