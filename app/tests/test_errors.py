from uuid import uuid4


def test_not_found_error(client, regular_headers):
    response = client.get("/api/v1/articles/999999", headers=regular_headers)
    assert response.status_code == 404
    assert response.json()["error"] == "Article not found"
    assert response.json()["code"] == 404
    assert response.json()["detail"] == "No article found with ID 999999"

    invalid_id = uuid4()
    response = client.get(f"/api/v1/users/{invalid_id}", headers=regular_headers)
    assert response.status_code == 404
    assert response.json()["error"] == "User not found"
    assert response.json()["code"] == 404
    assert response.json()["detail"] == f"No user found with ID {invalid_id}"


def test_validation_error(client, regular_headers):
    # Create a user with an invalid email and password
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "invalid-email", "username": "u", "password": "weak"},
    )
    print(f"Response: {response.json()}")
    assert response.status_code == 422
    assert response.json()["code"] == 422
    assert "detail" in response.json()
    assert any(error["field"] == "body.email" for error in response.json()["detail"])

    # Look for a user with an invalid id
    response = client.get("/api/v1/users/not-a-uuid", headers=regular_headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "uuid_parsing"
