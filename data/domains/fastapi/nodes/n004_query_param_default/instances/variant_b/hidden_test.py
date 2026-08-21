from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_defaults_applied():
    assert client.get("/products").json() == {"sort": "asc", "page": 1}


def test_values_echoed():
    assert client.get("/products?sort=desc&page=3").json() == {"sort": "desc", "page": 3}


def test_wrong_type_is_422():
    assert client.get("/products?page=xyz").status_code == 422
