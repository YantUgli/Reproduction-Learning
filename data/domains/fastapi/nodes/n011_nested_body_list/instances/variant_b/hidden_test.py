from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)

RECIPE = {
    "title": "roti",
    "ingredients": [{"name": "tepung", "grams": 500}, {"name": "gula", "grams": 50}],
}


def test_valid_recipe_201_with_total():
    r = client.post("/recipes", json=RECIPE)
    assert r.status_code == 201
    assert r.json() == {"title": "roti", "total_grams": 550}


def test_empty_ingredients_totals_zero():
    r = client.post("/recipes", json={"title": "air", "ingredients": []})
    assert r.status_code == 201
    assert r.json() == {"title": "air", "total_grams": 0}


def test_bad_nested_field_is_422():
    bad = {"title": "roti", "ingredients": [{"name": "tepung", "grams": "banyak"}]}
    assert client.post("/recipes", json=bad).status_code == 422


def test_ingredients_not_a_list_is_422():
    assert client.post("/recipes", json={"title": "roti", "ingredients": {}}).status_code == 422
