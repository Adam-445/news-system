import pytest
from fastapi import status
from uuid import UUID, uuid4


def test_get_all_users(client, admin_headers):
    response = client.get("/api/v1/users/", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 3


def test_search_users_by_email(client, admin_headers):
    response = client.get(
        "/api/v1/users/search",
        params={"email": "regular@example.com"},
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_admin_delete_user(client, admin_headers):
    # Create temporary user to delete
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "temp@example.com",
            "username": "tempuser",
            "password": "TempPass123!",
        },
    )
    user = response.json()
    response = client.delete(f"/api/v1/users/{user['id']}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_regular_user_cannot_delete(client, regular_headers):
    response = client.delete(
        f"/api/v1/users/{UUID(int=0)}",  # Tests permission first
        headers=regular_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_user_preferences(client, admin_headers, test_user):
    update_data = {"preferred_sources": ["BBC", "Reuters"]}
    response = client.put(
        "/api/v1/users/preferences",
        json=update_data,
        params={"user_id": test_user["id"]},
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["preferred_sources"] == ["BBC", "Reuters"]


def test_user_soft_delete(client, admin_headers, regular_headers, test_user):
    user_id = test_user["id"]

    # Delete user
    delete_response = client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)

    # Verify Deletion
    assert delete_response.status_code == 204
    
    # Retrieve user as an admin
    user_response = client.get(f"api/v1/users/{user_id}", headers=admin_headers)
    assert user_response.json()["is_deleted"] is True

    # Verify non-existence for regular users
    response = client.get(f"api/v1/users/{user_id}", headers=regular_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_reactivate_deleted_user(client, admin_headers, test_user):
    # Delete user
    test_user_id = test_user["id"]

    client.delete(f"/api/v1/users/{test_user_id}", headers=admin_headers)

    # Reactivate
    response = client.patch(
        f"/api/v1/users/undelete/{test_user_id}", headers=admin_headers
    )
    assert response.status_code == 204

    # Verify reactivation
    response = client.get(
        f"/api/v1/users/{test_user_id}", headers=admin_headers
    )
    assert response.json()["is_deleted"] is False


def test_delete_already_deleted_user(client, admin_headers, test_user):
    user_id = test_user["id"]
    # First delete
    client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    # Second delete
    response = client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_undelete_invalid_user(client, admin_headers):
    invalid_id = uuid4()
    response = client.patch(
        f"/api/v1/users/undelete/{invalid_id}", headers=admin_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND