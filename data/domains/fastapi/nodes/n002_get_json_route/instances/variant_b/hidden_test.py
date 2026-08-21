from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)


def test_status_code_200():
    assert client.get("/info").status_code == 200


def test_body_exact():
    assert client.get("/info").json() == {"service": "users", "version": 2}
