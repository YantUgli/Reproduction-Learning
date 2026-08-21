from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_valid_body_returns_201_echo():
    r = client.post("/items", json={"name": "pen", "price": 3.5})
    assert r.status_code == 201
    assert r.json() == {"name": "pen", "price": 3.5}


def test_missing_field_is_422():
    assert client.post("/items", json={"name": "pen"}).status_code == 422


def test_wrong_type_is_422():
    assert client.post("/items", json={"name": "pen", "price": "free"}).status_code == 422
