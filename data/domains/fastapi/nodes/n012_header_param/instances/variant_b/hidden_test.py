from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_both_headers_echoed():
    r = client.get("/ping", headers={"x-api-key": "k1", "x-client": "cli"})
    assert r.status_code == 200
    assert r.json() == {"key": "k1", "client": "cli"}


def test_optional_header_uses_default():
    r = client.get("/ping", headers={"x-api-key": "k1"})
    assert r.status_code == 200
    assert r.json() == {"key": "k1", "client": "unknown"}


def test_missing_required_header_is_422():
    assert client.get("/ping").status_code == 422
