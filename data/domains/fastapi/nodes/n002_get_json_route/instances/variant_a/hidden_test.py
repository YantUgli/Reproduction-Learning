from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_status_code_200():
    assert client.get("/status").status_code == 200


def test_body_exact():
    assert client.get("/status").json() == {"service": "orders", "ok": True}
