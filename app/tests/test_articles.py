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


def test_get_article_by_id(client, moderator_headers, regular_headers):
    # Create test article first
    client.post(
        "/api/v1/articles/",
        json={"title": "Test", "content": "Content", "url": "https://test.com"},
        headers=moderator_headers,
    )

    response = client.get("/api/v1/articles/1", headers=regular_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test"
    assert data["content"] == "Content"
    assert len(data) > 0


def test_article_not_found(client, regular_headers):
    response = client.get("/api/v1/articles/9999", headers=regular_headers)
    assert response.status_code == 404
    assert "Article with ID 9999 was not found" in response.json()["detail"]

def test_invalid_article_id(client, regular_headers):
    # Non-integer id
    response = client.get("/api/v1/articles/invalid_id", headers=regular_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative id
    response = client.get("/api/v1/articles/-1", headers=regular_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


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


def test_invalid_pagination(client, moderator_headers):
    # Negative `skip` or `limit`
    response = client.get(
        "/api/v1/articles/",
        params={"skip": -5, "limit": -10},
        headers=moderator_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_filter_articles_by_category(client, moderator_headers):
    # Create test articles
    client.post(
        "/api/v1/articles/",
        json={
            "title": "Tech Article",
            "content": "AI breakthroughs",
            "url": "https://tech.com/1",
            "category": "Technology",
        },
        headers=moderator_headers,
    )

    client.post(
        "/api/v1/articles/",
        json={
            "title": "Sports Article",
            "content": "World Cup",
            "url": "https://sports.com/1",
            "category": "Sports",
        },
        headers=moderator_headers,
    )

    # Filter by category
    response = client.get("/api/v1/articles/", params={"category": "Technology"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["category"] == "Technology"


def test_full_text_search(client, moderator_headers):
    client.post(
        "/api/v1/articles/",
        json={
            "title": "Python Tutorial",
            "content": "Learn Python programming",
            "url": "https://python.org/1",
            "category": "Education",
        },
        headers=moderator_headers,
    )

    response = client.get("/api/v1/articles/", params={"keyword": "Python"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "Python" in response.json()[0]["title"]


def test_invalid_date_filter(client, moderator_headers):
    # invalid date format
    response = client.get(
        "/api/v1/articles/",
        params={"start_date": "2025-02-XX", "end_date": "2025-02-YY"},
        headers=moderator_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_invalid_sort_parameters(client, moderator_headers):
    # Invalid `sort_by` column
    response = client.get(
        "/api/v1/articles/",
        params={"sort_by": "invalid_column", "order": "desc"},
        headers=moderator_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


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


def test_recommendations_prioritize_popularity(
    client, db, regular_headers, admin_headers
):
    # Set preferences
    client.put(
        "/api/v1/users/preferences",
        json={"preferred_categories": ["Tech"], "preferred_sources": ["BBC"]},
        headers=regular_headers,
    )

    # Create articles with varying views
    _create_test_article(
        client, db, admin_headers, "Low Views", "Tech", "BBC", views=10
    )
    _create_test_article(
        client, db, admin_headers, "High Views", "Tech", "BBC", views=100
    )

    # Fetch recommendations
    response = client.get("/api/v1/articles/recommendations", headers=regular_headers)
    assert response.status_code == 200
    assert response.json()[0]["title"] == "High Views"  # Most popular first


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
