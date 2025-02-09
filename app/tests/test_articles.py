from fastapi import status

from app.db import models


def _create_test_article(client, db, headers, title, category, source, views=0):
    article = {
        "title": title,
        "content": "Content",
        "url": f"https://{source}/{title}",
        "category": category,
        "source": source,
    }
    response = client.post("/api/v1/articles/", json=article, headers=headers)
    # Manually set views (since the endpoint increments on GET)
    db_article = db.query(models.Article).filter(models.Article.title == title).first()
    db_article.views = views
    db.commit()
    return response.json()


def test_moderator_can_create_article(client, moderator_headers):
    article_data = {
        "title": "Moderator Article",
        "content": "Moderator content",
        "url": "https://moderator.com",
    }
    response = client.post(
        "/api/v1/articles/", json=article_data, headers=moderator_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == article_data["title"]
    assert "id" in data
    assert "created_at" in data


def test_regular_user_cannot_create_article(client, regular_headers):
    article_data = {
        "title": "Regular User Article",
        "content": "Regular content",
        "url": "https://regular.com",
    }
    response = client.post(
        "/api/v1/articles/", json=article_data, headers=regular_headers
    )
    assert response.status_code == 403


def test_get_articles(client, moderator_headers, regular_headers):
    # Create test article first
    client.post(
        "/api/v1/articles/",
        json={"title": "Test", "content": "Content", "url": "https://test.com"},
        headers=moderator_headers,
    )

    response = client.get("/api/v1/articles/", headers=regular_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_article_not_found(client, regular_headers):
    response = client.get("/api/v1/articles/9999", headers=regular_headers)
    assert response.status_code == 404
    assert "Article with id 9999" in response.json()["detail"]


def test_admin_can_delete_article(client, admin_headers, moderator_headers):
    # Create article
    article = client.post(
        "/api/v1/articles/",
        json={"title": "Test", "content": "Content", "url": "https://test.com"},
        headers=moderator_headers,
    ).json()

    # Delete as admin
    response = client.delete(f"/api/v1/articles/{article['id']}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_article_pagination(client, moderator_headers):
    # Create multiple articles
    for i in range(15):
        client.post(
            "/api/v1/articles/",
            json={
                "title": f"Article {i}",
                "content": "Content",
                "url": f"https://test.com/{i}",
            },
            headers=moderator_headers,
        )

    response = client.get(
        "/api/v1/articles/", params={"skip": 5, "limit": 5}, headers=moderator_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 5
    assert "X-Total-Count" in response.headers
    assert int(response.headers["X-Total-Count"]) == 15


def test_scrape_articles_permissions(client, regular_headers, moderator_headers):
    # Regular user
    response = client.post("/api/v1/articles/scrape", headers=regular_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Moderator
    response = client.post("/api/v1/articles/scrape", headers=moderator_headers)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_get_recommendations(client, regular_headers, admin_headers):
    # Set user preferences
    client.put(
        "/api/v1/users/preferences",
        json={"preferred_categories": ["Technology"], "preferred_sources": ["BBC"]},
        headers=regular_headers,
    )

    # Create matching article
    client.post(
        "/api/v1/articles/",
        json={
            "title": "Test Tech",
            "content": "Content",
            "url": "https://bbc.com/tech",
            "category": "Technology",
            "source": "BBC",
        },
        headers=admin_headers,
    )

    # Fetch recommendations
    response = client.get("/api/v1/articles/recommendations", headers=regular_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["category"] == "Technology"


def test_empty_recommendations(client, regular_headers):
    response = client.get("/api/v1/articles/recommendations", headers=regular_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_recommendations_prioritize_popularity(client, db, regular_headers, admin_headers):
    # Set preferences
    client.put(
        "/api/v1/users/preferences",
        json={"preferred_categories": ["Tech"], "preferred_sources": ["BBC"]},
        headers=regular_headers,
    )

    # Create articles with varying views
    _create_test_article(client, db, admin_headers, "Low Views", "Tech", "BBC", views=10)
    _create_test_article(client, db, admin_headers, "High Views", "Tech", "BBC", views=100)

    # Fetch recommendations
    response = client.get("/api/v1/articles/recommendations", headers=regular_headers)
    assert response.status_code == 200
    assert response.json()[0]["title"] == "High Views"  # Most popular first
