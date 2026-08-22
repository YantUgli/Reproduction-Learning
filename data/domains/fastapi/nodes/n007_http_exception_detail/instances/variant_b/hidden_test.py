from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_ok_room_booked():
    r = client.post("/rooms/r202")
    assert r.status_code == 200
    assert r.json() == {"code": "r202"}


def test_conflict_is_409_with_detail():
    r = client.post("/rooms/r101")
    assert r.status_code == 409
    assert r.json() == {"detail": "room already booked"}


def test_short_code_is_400_with_detail():
    r = client.post("/rooms/r1")
    assert r.status_code == 400
    assert r.json() == {"detail": "code too short"}
