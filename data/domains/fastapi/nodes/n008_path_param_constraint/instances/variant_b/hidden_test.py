from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_valid_page_ok():
    r = client.get("/pages/12")
    assert r.status_code == 200
    assert r.json() == {"page_no": 12}


def test_zero_is_422():
    assert client.get("/pages/0").status_code == 422


def test_negative_is_422():
    assert client.get("/pages/-1").status_code == 422


def test_non_integer_is_422():
    assert client.get("/pages/xyz").status_code == 422
