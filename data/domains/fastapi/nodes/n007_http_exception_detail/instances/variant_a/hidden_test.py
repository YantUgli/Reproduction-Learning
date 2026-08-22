from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_ok_account_created():
    r = client.post("/accounts/ada")
    assert r.status_code == 200
    assert r.json() == {"name": "ada"}


def test_conflict_is_409_with_detail():
    r = client.post("/accounts/admin")
    assert r.status_code == 409
    assert r.json() == {"detail": "account already exists"}


def test_short_name_is_400_with_detail():
    r = client.post("/accounts/ab")
    assert r.status_code == 400
    assert r.json() == {"detail": "name too short"}
