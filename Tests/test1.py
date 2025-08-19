from fastapi.testclient import TestClient
from pydantic import BaseModel
from app import app
from validation import *

client_test = TestClient(app)


def test_login_user():
    payload = {
        "username": "testuser",
        "password": "testpass"
    }

    response = client_test.post("/student/login", json=payload)
    print("Response JSON:", response.json())

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "user" in data
    assert "token" in data

    user = data["user"]
    token = data["token"]

    parsed_user = StudentLogin(**user)
    parsed_token = Token(**token)

    assert parsed_user.username == "testuser"
    assert parsed_token.token_type.lower() == "bearer"
    assert parsed_token.access_token == token["access_token"]
