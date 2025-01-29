def test_get_users(client, auth_headers):
    response = client.get("/api/v1/users/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_user_soft_delete(client, auth_headers, test_user):
    user_id = test_user["id"]
    
    # Delete user
    delete_response = client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    
    # Verify soft delete 
    response = client.get("/api/v1/users/", headers=auth_headers)
    users = [u for u in response.json() if u["id"] == user_id]
    assert len(users) == 0

def test_user_undelete(client, auth_headers, test_user):
    user_id = test_user["id"]
    
    # Delete and undelete
    client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    response = client.patch(f"/api/v1/users/undelete/{user_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verify restoration
    response = client.get("/api/v1/users/search", headers=auth_headers, params=[("id", user_id)])
    assert response.json()[0]["is_active"] is True

def test_user_search(client, auth_headers, test_user):
    response = client.get(
        "/api/v1/users/search",
        params={"email": "test@example.com"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "test@example.com"