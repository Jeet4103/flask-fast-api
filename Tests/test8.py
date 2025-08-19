from fastapi.testclient import TestClient
from app import app

client_test = TestClient(app)

def test_advanced_search():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NCIsImV4cCI6MTc1NDYzNjQ0NH0.27i1PAUAubeEkzcY02HRK5TGgWU34w7OHws5MArPbQQ"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "query": "",
        "sort_by": "id",
        "sort_order": "asc"
    }
    response = client_test.get("/student/search/", headers=headers, params=payload)
    print("Response JSON:", response.json())
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "users" in data

    for student in data["users"]:
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
  
          

