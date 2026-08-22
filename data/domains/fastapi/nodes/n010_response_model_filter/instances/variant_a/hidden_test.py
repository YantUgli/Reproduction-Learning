from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)

PAYLOAD = {"username": "ada", "password": "s3cret", "email": "ada@example.com"}


def test_created_201():
    assert client.post("/users", json=PAYLOAD).status_code == 201


def test_response_filtered_to_declared_fields():
    assert client.post("/users", json=PAYLOAD).json() == {
        "username": "ada",
        "email": "ada@example.com",
    }


def test_password_never_leaks():
    assert "password" not in client.post("/users", json=PAYLOAD).json()


def test_missing_input_field_is_422():
    assert client.post("/users", json={"username": "ada", "password": "s3cret"}).status_code == 422
