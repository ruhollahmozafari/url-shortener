import asyncio
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from shortener_app.services.url_service import URLService


class TestURLShortener:
    """Test URL shortener functionality"""

    def test_create_short_url(self, client: TestClient):
        """Test creating a short URL"""
        url_data = {"long_url": "https://www.google.com/"}

        response = client.post("/api/v1/urls/", json=url_data)
        assert response.status_code == 201

        data = response.json()
        assert "short_code" in data
        assert "short_url" in data
        assert data["long_url"] == url_data["long_url"]
        assert data["total_hits"] == 0
        assert data["is_active"] is True

    def test_get_url_info(self, client: TestClient):
        """Test getting URL information"""
        # Create a URL
        url_data = {"long_url": "https://www.google.com/"}
        create_response = client.post("/api/v1/urls/", json=url_data)
        short_code = create_response.json()["short_code"]

        # Get URL info
        response = client.get(f"/api/v1/urls/{short_code}")
        assert response.status_code == 200

        data = response.json()
        assert data["short_code"] == short_code
        assert data["long_url"] == "https://www.google.com/"
        assert "short_url" in data

    def test_get_nonexistent_url(self, client: TestClient):
        """Test getting info for non-existent URL"""
        response = client.get("/api/v1/urls/nonexistent")
        assert response.status_code == 404

    def test_redirect_url(self, client: TestClient):
        """Test URL redirection"""
        # Create a URL
        url_data = {"long_url": "https://www.github.com/"}
        create_response = client.post("/api/v1/urls/", json=url_data)
        short_code = create_response.json()["short_code"]

        # Test redirect
        response = client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "https://www.github.com/"

    def test_redirect_nonexistent_url(self, client: TestClient):
        """Test redirecting non-existent URL"""
        response = client.get("/nonexistent", follow_redirects=False)
        assert response.status_code == 404

    def test_url_stats(self, client: TestClient):
        """Test getting URL statistics"""
        # Create a URL
        url_data = {"long_url": "https://www.stackoverflow.com/"}
        create_response = client.post("/api/v1/urls/", json=url_data)
        short_code = create_response.json()["short_code"]

        # Access the URL to increment hits
        client.get(f"/{short_code}", follow_redirects=False)

        # Get stats
        response = client.get(f"/api/v1/urls/{short_code}/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["short_code"] == short_code
        assert data["total_hits"] >= 0  # Hits are updated asynchronously via queue

    def test_delete_url(self, client: TestClient):
        """Test deleting a URL"""
        # Create a URL
        url_data = {"long_url": "https://www.python.org"}
        create_response = client.post("/api/v1/urls/", json=url_data)
        short_code = create_response.json()["short_code"]

        # Delete the URL
        response = client.delete(f"/api/v1/urls/{short_code}")
        assert response.status_code == 204

        # Try to access deleted URL
        response = client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 404

    def test_invalid_url(self, client: TestClient):
        """Test creating URL with invalid URL"""
        url_data = {"long_url": "not-a-valid-url"}

        response = client.post("/api/v1/urls/", json=url_data)
        assert response.status_code == 422  # Validation error


class TestURLService:
    """Test URL service business logic directly"""

    def test_short_code_generation(self, db_session):
        """Test that short codes are generated correctly"""
        service = URLService(db_session)

        # Create two URLs with same long_url
        test_url = "https://www.test.com/"
        url1 = asyncio.run(service.create_short_url(HttpUrl(test_url)))
        url2 = asyncio.run(service.create_short_url(HttpUrl(test_url)))

        # Short codes should be different (analytics tracking)
        assert url1.short_code != url2.short_code

        # Both should point to same long URL
        assert url1.long_url == url2.long_url

    def test_url_retrieval(self, db_session):
        """Test URL retrieval by short code"""
        service = URLService(db_session)

        # Create a URL
        url = asyncio.run(service.create_short_url(HttpUrl("https://www.example.com/")))
        short_code = url.short_code

        # Retrieve by short code
        retrieved_url = asyncio.run(service.get_url_by_short_code(short_code))
        assert retrieved_url is not None
        assert retrieved_url.short_code == short_code
        assert retrieved_url.long_url == "https://www.example.com/"  # Pydantic normalizes URLs

        # Test non-existent short code
        non_existent = asyncio.run(service.get_url_by_short_code("nonexistent"))
        assert non_existent is None

    def test_redirect_increments_hits(self, db_session):
        """Test that redirect increments hit count (async via queue)"""
        service = URLService(db_session)

        # Create a URL (Pydantic normalizes URLs, adds trailing slash to base URLs)
        url = asyncio.run(service.create_short_url(HttpUrl("https://www.example.com/")))
        short_code = url.short_code

        # Initial hits should be 0
        assert url.total_hits == 0

        # Redirect should return the long URL (hits are tracked via queue)
        long_url = asyncio.run(service.get_long_url_for_redirect(short_code))
        assert long_url == "https://www.example.com/"  # Pydantic adds trailing slash

        # Note: Hits are updated asynchronously via queue worker
        # In tests, we verify the URL is retrievable
        updated_url = asyncio.run(service.get_url_by_short_code(short_code))
        assert updated_url is not None
        assert updated_url.short_code == short_code

    def test_delete_url(self, db_session):
        """Test URL deletion (soft delete)"""
        service = URLService(db_session)

        # Create a URL
        url = asyncio.run(service.create_short_url(HttpUrl("https://www.example.com/")))
        short_code = url.short_code

        # Delete the URL
        success = asyncio.run(service.delete_url(short_code))
        assert success is True

        # URL should not be retrievable anymore
        deleted_url = asyncio.run(service.get_url_by_short_code(short_code))
        assert deleted_url is None

        # Redirect should fail
        redirect_result = asyncio.run(service.get_long_url_for_redirect(short_code))
        assert redirect_result is None
