from fastapi.testclient import TestClient
from app import app

client_test = TestClient(app)

def test_delete_user():
    id = 53
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NCIsImV4cCI6MTc1NDYzNTcyNn0.OlDephYLB-stWfh7hl7sCfnk22--bN2eLwOIWkbjmQo"
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