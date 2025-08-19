from fastapi.testclient import TestClient
from pydantic import BaseModel
from app import app
from validation import *

client_test = TestClient(app)

def test_logedin_student():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NCIsImV4cCI6MTc1NDYzNDA2Nn0.IwKcxiNrmj1NUpRd18P5-NLr2pqXfDQ_sk54NrtYFu4"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client_test.get("/logedin/student", headers=headers)
    print("Response JSON:", response.json())

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "id" in data
    assert "first_name" in data
    assert "last_name" in data
    assert "full_name" in data
    assert "email" in data
    assert "username" in data
    assert "role" in data

    if data["role"] == "student":
        assert "student_info" in data
        assert "staff_info" not in data
    elif data["role"] == "staff":
        assert "staff_info" in data
        assert "student_info" not in data
    else:
        raise AssertionError(f"Unexpected role: {data['role']}")



