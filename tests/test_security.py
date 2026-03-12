from app import security


def test_verify_api_key_when_auth_disabled(monkeypatch):
    monkeypatch.setattr(security, "API_KEY", "")
    assert security.verify_api_key(None) is True


def test_verify_api_key_when_auth_enabled(monkeypatch):
    monkeypatch.setattr(security, "API_KEY", "secret")
    assert security.verify_api_key("secret") is True
    assert security.verify_api_key("bad") is False
