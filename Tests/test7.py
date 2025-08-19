from fastapi.testclient import TestClient
from app import app

client_test = TestClient(app)

def test_update_user_profile():
    id = 47
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NCIsImV4cCI6MTc1NDYzMzQxMn0.slcTCtlz-Y0NzKP1Gv2UG3_KuS4dDhrR_gLUYrEEWmM"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "phone_number": 1234567890,
        "mothers_name": "mother's name",
        "fathers_name": "father's name",
        "date_of_birth": "1990-01-01",
        "address": "address",
        "branch": "branch"
    }

    response = client_test.patch(f"/user/profile", headers=headers, json=payload)