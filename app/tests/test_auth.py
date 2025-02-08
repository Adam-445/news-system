from fastapi import status

def test_successful_signup(client):
    user_data = {
        "email": "new@example.com",
        "username": "newuser",
        "password": "ValidPass123!"
    }
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()
    assert "password" not in response.json()

def test_signup_duplicate_username(client):
    user_data = {
        "email": "unique@example.com",
        "username": "admin_user",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == status.HTTP_409_CONFLICT

def test_login_success(client):
    credentials = {"username": "admin_user", "password": "TestPass123!"}
    response = client.post("/api/v1/auth/login", data=credentials)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

def test_login_invalid_credentials(client):
    credentials = {"username": "admin_user", "password": "wrongpassword"}
    response = client.post("/api/v1/auth/login", data=credentials)
    assert response.status_code == status.HTTP_403_FORBIDDEN