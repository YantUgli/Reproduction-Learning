from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_defaults_on_first_route():
    r = client.get("/posts")
    assert r.status_code == 200
    assert r.json() == {"page": 1, "size": 20, "offset": 0}


def test_same_dependency_on_second_route():
    r = client.get("/comments?page=3&size=10")
    assert r.status_code == 200
    assert r.json() == {"page": 3, "size": 10, "offset": 20}


def test_offset_computed_from_params():
    assert client.get("/posts?page=2&size=25").json()["offset"] == 25


def test_bad_type_is_422():
    assert client.get("/posts?page=abc").status_code == 422
