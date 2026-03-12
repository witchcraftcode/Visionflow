from app import security


def test_verify_api_key_when_auth_disabled(monkeypatch):
    monkeypatch.setattr(security, "API_KEY", "")
    assert security.verify_api_key(None) is True


def test_verify_api_key_when_auth_enabled(monkeypatch):
    monkeypatch.setattr(security, "API_KEY", "secret")
    assert security.verify_api_key("secret") is True
    assert security.verify_api_key("bad") is False


def test_verify_admin_key_when_disabled(monkeypatch):
    monkeypatch.setattr(security, "API_KEY", "")
    monkeypatch.setattr(security, "ADMIN_API_KEY", "")
    assert security.verify_admin_key(None) is True


def test_verify_admin_key_when_enabled(monkeypatch):
    monkeypatch.setattr(security, "API_KEY", "user-secret")
    monkeypatch.setattr(security, "ADMIN_API_KEY", "admin-secret")
    assert security.verify_admin_key("admin-secret") is True
    assert security.verify_admin_key("user-secret") is False


def test_allow_request_uses_redis_rate_limit(monkeypatch):
    calls = []

    def fake_consume_rate_limit(client_id, limit, window_seconds):
        calls.append((client_id, limit, window_seconds))
        return True

    monkeypatch.setattr(security, "consume_rate_limit", fake_consume_rate_limit)
    monkeypatch.setattr(security, "RATE_LIMIT_REQUESTS", 12)
    monkeypatch.setattr(security, "RATE_LIMIT_WINDOW_SECONDS", 30)

    assert security.allow_request("client-1") is True
    assert calls == [("client-1", 12, 30)]
