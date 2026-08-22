from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_valid_id_ok():
    r = client.get("/items/5")
    assert r.status_code == 200
    assert r.json() == {"item_id": 5}


def test_zero_is_422():
    assert client.get("/items/0").status_code == 422


def test_negative_is_422():
    assert client.get("/items/-3").status_code == 422


def test_non_integer_is_422():
    assert client.get("/items/abc").status_code == 422
