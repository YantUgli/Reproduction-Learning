from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_both_headers_echoed():
    r = client.get("/whoami", headers={"x-token": "abc", "x-trace": "t1"})
    assert r.status_code == 200
    assert r.json() == {"token": "abc", "trace": "t1"}


def test_optional_header_defaults_to_none():
    r = client.get("/whoami", headers={"x-token": "abc"})
    assert r.status_code == 200
    assert r.json() == {"token": "abc", "trace": None}


def test_missing_required_header_is_422():
    assert client.get("/whoami").status_code == 422
