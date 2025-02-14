def test_not_found_error(client, regular_headers):
    response = client.get("/api/v1/articles/999999", headers=regular_headers)
    assert response.status_code == 404
    assert response.json() == {
        "error": "article not found",
        "code": 404,
        "detail": "No article with ID 999999",
    }


def test_validation_error(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "invalid-email", "username": "u", "password": "weak"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()
    assert any(error["field"] == "email" for error in response.json()["detail"])