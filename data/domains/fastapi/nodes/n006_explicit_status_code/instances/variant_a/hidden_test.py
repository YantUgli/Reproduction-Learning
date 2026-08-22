from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_post_returns_202_with_body():
    r = client.post("/jobs")
    assert r.status_code == 202
    assert r.json() == {"queued": True}


def test_delete_returns_204():
    assert client.delete("/jobs/7").status_code == 204


def test_delete_body_is_empty():
    assert client.delete("/jobs/7").content == b""
