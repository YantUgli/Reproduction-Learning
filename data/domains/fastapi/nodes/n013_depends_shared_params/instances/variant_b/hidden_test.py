from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_defaults_on_first_route():
    r = client.get("/books")
    assert r.status_code == 200
    assert r.json() == {"sort": "asc", "limit": 5, "reverse": False}


def test_same_dependency_on_second_route():
    r = client.get("/films?sort=desc&limit=2")
    assert r.status_code == 200
    assert r.json() == {"sort": "desc", "limit": 2, "reverse": True}


def test_reverse_follows_sort():
    assert client.get("/books?sort=desc").json()["reverse"] is True


def test_bad_type_is_422():
    assert client.get("/books?limit=abc").status_code == 422
