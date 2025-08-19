from fastapi.testclient import TestClient
from app import app

client_test = TestClient(app)

def test_soft_delete_student():
    id = 47
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NCIsImV4cCI6MTc1NDYzNTI2M30.n-QulV7bHScx7UYjc-DV53S8SGa-a1A1ZmMZegppjaE"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client_test.delete(f"/student/{id}", headers=headers)
    print("Status:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "message" in data
    assert data["message"] == "Student deleted successfully"
