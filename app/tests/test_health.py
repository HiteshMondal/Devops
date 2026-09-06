def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "app" in body
    assert "env" in body


def test_health_versioned_alias(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_config_hides_secrets(client):
    resp = client.get("/config")
    assert resp.status_code == 200
    body = resp.json()
    for secret_key in ("jwt_secret", "api_key", "session_secret", "db_password"):
        assert secret_key not in body