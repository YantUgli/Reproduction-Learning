from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)

ORDER = {"customer": "ada", "lines": [{"sku": "A", "qty": 2}, {"sku": "B", "qty": 3}]}


def test_valid_order_201_with_total():
    r = client.post("/orders", json=ORDER)
    assert r.status_code == 201
    assert r.json() == {"customer": "ada", "total_qty": 5}


def test_empty_lines_totals_zero():
    r = client.post("/orders", json={"customer": "ada", "lines": []})
    assert r.status_code == 201
    assert r.json() == {"customer": "ada", "total_qty": 0}


def test_bad_nested_field_is_422():
    bad = {"customer": "ada", "lines": [{"sku": "A", "qty": "two"}]}
    assert client.post("/orders", json=bad).status_code == 422


def test_lines_not_a_list_is_422():
    assert client.post("/orders", json={"customer": "ada", "lines": {}}).status_code == 422
