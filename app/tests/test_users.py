import pytest
from fastapi import status
from uuid import UUID

def test_get_all_users(client, admin_headers):
    response = client.get("/api/v1/users/", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 3

def test_search_users_by_email(client, admin_headers):
    response = client.get(
        "/api/v1/users/search",
        params={"email": "regular@example.com"},
        headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

def test_admin_delete_user(client, admin_headers):
    # Create temporary user to delete
    user = client.post("/api/v1/auth/signup", json={
        "email": "temp@example.com",
        "username": "tempuser",
        "password": "TempPass123!"
    }).json()
    
    response = client.delete(
        f"/api/v1/users/{user['id']}",
        headers=admin_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_regular_user_cannot_delete(client, regular_headers):
    response = client.delete(
        f"/api/v1/users/{UUID(int=0)}",  # Tests permission first
        headers=regular_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

# def test_update_user_preferences(client, admin_headers, test_user):
#     update_data = {"preferred_sources": ["BBC", "Reuters"]}
#     response = client.patch(
#         "/api/v1/users/preferences",
#         json=update_data,
#         params={"user_id": test_user["id"]},
#         headers=admin_headers
#     )
#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["preferred_sources"] == ["BBC", "Reuters"]

def test_user_soft_delete(client, admin_headers, test_user):
    user_id = test_user["id"]
    
    # Delete user
    delete_response = client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert delete_response.status_code == 204
    
    # Verify soft delete 
    response = client.get("/api/v1/users/", headers=admin_headers)
    users = [u for u in response.json() if u["id"] == user_id]
    assert len(users) == 0

def test_user_undelete(client, admin_headers, test_user):
    user_id = test_user["id"]
    
    # Delete and undelete
    client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    response = client.patch(f"/api/v1/users/undelete/{user_id}", headers=admin_headers)
    assert response.status_code == 204
    
    # Verify restoration
    response = client.get("/api/v1/users/search", headers=admin_headers, params=[("id", user_id)])
    assert response.json()[0]["is_active"] is True