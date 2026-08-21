from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_valid_body_returns_201_echo():
    r = client.post("/users", json={"name": "ada", "age": 30})
    assert r.status_code == 201
    assert r.json() == {"name": "ada", "age": 30}


def test_missing_field_is_422():
    assert client.post("/users", json={"name": "ada"}).status_code == 422


def test_wrong_type_is_422():
    assert client.post("/users", json={"name": "ada", "age": "old"}).status_code == 422
