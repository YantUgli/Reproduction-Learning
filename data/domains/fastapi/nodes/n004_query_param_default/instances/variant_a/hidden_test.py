from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_defaults_applied():
    assert client.get("/search").json() == {"q": "", "limit": 10}


def test_values_echoed():
    assert client.get("/search?q=book&limit=5").json() == {"q": "book", "limit": 5}


def test_wrong_type_is_422():
    assert client.get("/search?limit=abc").status_code == 422
