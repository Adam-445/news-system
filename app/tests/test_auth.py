def test_user_signup(client):
    user_data = {
        "email": "new@example.com",
        "username": "newuser",
        "password": "NewPass123!"
    }
    
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "password" not in data

def test_duplicate_user_signup(client, test_user):
    response = client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "Password123!"
    })
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

def test_valid_login(client, test_user):
    response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_invalid_login(client):
    response = client.post("/api/v1/auth/login", data={
        "username": "wronguser",
        "password": "wrongpass"
    })
    assert response.status_code == 403
    assert "Invalid Credentails" in response.json()["detail"]