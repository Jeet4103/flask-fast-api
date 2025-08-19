from fastapi.testclient import TestClient
from pydantic import BaseModel
from app import app
from validation import *

client_test = TestClient(app)

def test_get_all_students():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NCIsImV4cCI6MTc1NDYzMzQxMn0.slcTCtlz-Y0NzKP1Gv2UG3_KuS4dDhrR_gLUYrEEWmM"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client_test.get("/students/", headers=headers)
    print("Response JSON:", response.json())
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data

    for student in data["items"]:
        assert "id" in student
        assert "username" in student
        assert "email" in student
        assert "role" in student
        assert "first_name" in student
        assert "last_name" in student
        assert "full_name" in student

        if student["role"] == "student":
            assert "student_info" in student
        elif student["role"] == "staff":
            assert "staff_info" in student
