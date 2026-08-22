from fastapi.testclient import TestClient
from solution import app

client = TestClient(app)

PAYLOAD = {"name": "budi", "salary": 9000, "department": "ops"}


def test_created_201():
    assert client.post("/employees", json=PAYLOAD).status_code == 201


def test_response_filtered_to_declared_fields():
    assert client.post("/employees", json=PAYLOAD).json() == {
        "name": "budi",
        "department": "ops",
    }


def test_salary_never_leaks():
    assert "salary" not in client.post("/employees", json=PAYLOAD).json()


def test_missing_input_field_is_422():
    assert client.post("/employees", json={"name": "budi", "salary": 9000}).status_code == 422
