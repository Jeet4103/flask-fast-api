from fastapi.testclient import TestClient
from app import app

client_test = TestClient(app)

def test_student_by_id():
    id = 47
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NCIsImV4cCI6MTc1NDYzMzQxMn0.slcTCtlz-Y0NzKP1Gv2UG3_KuS4dDhrR_gLUYrEEWmM"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client_test.get(f"/student/{id}", headers=headers)
    print("Response JSON:", response.json())

    assert response.status_code == 200

    student = response.json()
    assert isinstance(student, dict)

    assert "id" in student
    assert "username" in student
    assert "email" in student
    assert "role" in student
    assert "first_name" in student
    assert "last_name" in student
    assert "full_name" in student

    if student["role"] == "student":
        assert "student_info" in student
        assert "staff_info" not in student
    elif student["role"] == "staff":
        assert "staff_info" in student
        assert "student_info" not in student
    