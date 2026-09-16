from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_default_when_no_cookie():
    r = client.get("/cart")
    assert r.status_code == 200
    assert r.json() == {"cart_count": 0}


def test_reads_provided_cookie():
    r = client.get("/cart", cookies={"cart_count": "5"})
    assert r.status_code == 200
    assert r.json() == {"cart_count": 5}


def test_ignores_unrelated_cookies():
    r = client.get("/cart", cookies={"other": "value"})
    assert r.status_code == 200
    assert r.json() == {"cart_count": 0}


def test_another_value():
    r = client.get("/cart", cookies={"cart_count": "42"})
    assert r.status_code == 200
    assert r.json() == {"cart_count": 42}
