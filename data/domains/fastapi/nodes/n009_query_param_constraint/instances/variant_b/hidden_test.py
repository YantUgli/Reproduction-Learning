from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_default_page_applied():
    r = client.get("/users?name=ada")
    assert r.status_code == 200
    assert r.json() == {"name": "ada", "page": 1}


def test_boundary_page_allowed():
    assert client.get("/users?name=ada&page=20").json() == {"name": "ada", "page": 20}


def test_missing_required_query_is_422():
    assert client.get("/users").status_code == 422


def test_too_short_name_is_422():
    assert client.get("/users?name=a").status_code == 422


def test_page_out_of_range_is_422():
    assert client.get("/users?name=ada&page=21").status_code == 422
    assert client.get("/users?name=ada&page=0").status_code == 422
