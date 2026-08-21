from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_found_returns_200_and_body():
    r = client.get("/items/1")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "name": "apple"}


def test_missing_returns_404():
    assert client.get("/items/999").status_code == 404
