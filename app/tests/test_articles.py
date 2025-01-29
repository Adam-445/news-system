def test_create_article(client, auth_headers):
    article_data = {
        "title": "Test Article",
        "content": "This is a test article",
        "url": "https://test.com",
        "source": "Test News",
        "category": "Technology",
    }

    response = client.post("/api/v1/articles/", json=article_data, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == article_data["title"]
    assert "id" in data
    assert "created_at" in data


def test_get_articles(client, auth_headers):
    # Create test article first
    client.post(
        "/api/v1/articles/",
        json={"title": "Test", "content": "Content", "url": "https://test.com"},
        headers=auth_headers,
    )

    response = client.get("/api/v1/articles/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# def test_unauthorized_article_access(client):
#     response = client.get("/api/v1/articles/")
#     assert response.status_code == 401
#     assert "Not authenticated" in response.json()["detail"]

def test_article_not_found(client, auth_headers):
    response = client.get("/api/v1/articles/9999", headers=auth_headers)
    assert response.status_code == 404
    assert "Article with id 9999" in response.json()["detail"]
