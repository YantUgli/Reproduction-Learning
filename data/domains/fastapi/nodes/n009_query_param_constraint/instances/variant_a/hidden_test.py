from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_default_limit_applied():
    r = client.get("/search?q=book")
    assert r.status_code == 200
    assert r.json() == {"q": "book", "limit": 10}


def test_boundary_limit_allowed():
    assert client.get("/search?q=book&limit=50").json() == {"q": "book", "limit": 50}


def test_missing_required_query_is_422():
    assert client.get("/search").status_code == 422


def test_too_short_query_is_422():
    assert client.get("/search?q=ab").status_code == 422


def test_limit_out_of_range_is_422():
    assert client.get("/search?q=book&limit=51").status_code == 422
    assert client.get("/search?q=book&limit=0").status_code == 422
