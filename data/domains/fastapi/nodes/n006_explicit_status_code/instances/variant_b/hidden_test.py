from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_post_returns_202_with_body():
    r = client.post("/emails")
    assert r.status_code == 202
    assert r.json() == {"accepted": True}


def test_delete_returns_204():
    assert client.delete("/emails/12").status_code == 204


def test_delete_body_is_empty():
    assert client.delete("/emails/12").content == b""
