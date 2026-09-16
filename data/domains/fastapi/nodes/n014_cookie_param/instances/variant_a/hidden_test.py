from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_default_when_no_cookie():
    r = client.get("/profile")
    assert r.status_code == 200
    assert r.json() == {"session_id": "guest"}


def test_reads_provided_cookie():
    r = client.get("/profile", cookies={"session_id": "abc123"})
    assert r.status_code == 200
    assert r.json() == {"session_id": "abc123"}


def test_ignores_unrelated_cookies():
    r = client.get("/profile", cookies={"other": "value"})
    assert r.status_code == 200
    assert r.json() == {"session_id": "guest"}


def test_another_value():
    r = client.get("/profile", cookies={"session_id": "xyz-999"})
    assert r.status_code == 200
    assert r.json() == {"session_id": "xyz-999"}
