import pytest
from uuid import UUID, uuid4
from fastapi import status

def test_admin_can_change_user_role(client, admin_headers):
    # Create second test user
    user2 = client.post("/api/v1/auth/signup", json={
        "email": "user2@example.com",
        "username": "user2",
        "password": "TestPass123!"
    }).json()
    
    response = client.put(
        f"/api/v1/admin/users/{user2['id']}/roles",
        json={"role": "moderator"},
        headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["role_name"] == "moderator"

def test_non_admin_cannot_change_roles(client, regular_headers):
    user2 = client.post("/api/v1/auth/signup", json={
        "email": "user2@example.com",
        "username": "user2",
        "password": "TestPass123!"
    }).json()
    
    response = client.put(
        f"/api/v1/admin/users/{user2['id']}/roles",
        json={"role": "moderator"},
        headers=regular_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_change_role_invalid_user_id(client, admin_headers):
    invalid_id = uuid4()
    response = client.put(
        f"/api/v1/admin/users/{invalid_id}/roles",
        json={"role": "moderator"},
        headers=admin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_change_role_invalid_role(client, admin_headers, test_user):
    response = client.put(
        f"/api/v1/admin/users/{test_user["id"]}/roles",
        json={"role": "invalid_role"},
        headers=admin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_unauthenticated_access(client, test_user):
    response = client.put(
        f"/api/v1/admin/users/{test_user['id']}/roles",
        json={"role": "moderator"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_role_hierarchy(client, admin_headers, moderator_headers, regular_headers):
    # Admin can access moderator endpoints
    response = client.post(
        "/api/v1/articles/",
        json={"title": "Admin Article", "content": "Content", "url": "https://admin.com"},
        headers=admin_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    
    # Moderator cannot access admin endpoints
    response = client.put(
        f"/api/v1/admin/users/{UUID(int=0)}/roles",
        json={"role": "moderator"},
        headers=moderator_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Regular user cannot access moderator endpoints
    response = client.delete(
        f"/api/v1/articles/1",
        headers=regular_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_role_propagation(client, admin_headers):
    # Create and promote user
    user = client.post("/api/v1/auth/signup", json={
        "email": "promote@example.com",
        "username": "promote_me",
        "password": "TestPass123!"
    }).json()
    
    # Promote to moderator
    response = client.put(
        f"/api/v1/admin/users/{user['id']}/roles",
        json={"role": "moderator"},
        headers=admin_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Test new permissions
    headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', data={
        'username': 'promote_me',
        'password': 'TestPass123!'
    }).json()['access_token']}"}
    
    response = client.post(
        "/api/v1/articles/",
        json={"title": "New Article", "url": "https://new.com", "content": "Content"},
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED