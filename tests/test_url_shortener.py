import pytest
from fastapi.testclient import TestClient


class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns app info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data


class TestURLShortener:
    """Test URL shortener functionality"""
    
    def test_create_short_url(self, client: TestClient, sample_url_data):
        """Test creating a short URL"""
        response = client.post("/api/v1/urls/", json=sample_url_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "short_code" in data
        assert "short_url" in data
        assert data["long_url"] == sample_url_data["long_url"]
        assert data["hits"] == 0
        assert data["is_active"] is True
    
    def test_get_url_info(self, client: TestClient):
        """Test getting URL information"""
        # Create a URL
        url_data = {"long_url": "https://www.google.com"}
        create_response = client.post("/api/v1/urls/", json=url_data)
        short_code = create_response.json()["short_code"]
        
        # Get URL info
        response = client.get(f"/api/v1/urls/{short_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["short_code"] == short_code
        assert data["long_url"] == "https://www.google.com"
        assert "short_url" in data
    
    def test_get_nonexistent_url(self, client: TestClient):
        """Test getting info for non-existent URL"""
        response = client.get("/api/v1/urls/nonexistent")
        assert response.status_code == 404
    
    def test_redirect_url(self, client: TestClient):
        """Test URL redirection"""
        # Create a URL
        url_data = {"long_url": "https://www.github.com"}
        create_response = client.post("/api/v1/urls/", json=url_data)
        short_code = create_response.json()["short_code"]
        
        # Test redirect
        response = client.get(f"/{short_code}", allow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "https://www.github.com"
    
    def test_redirect_nonexistent_url(self, client: TestClient):
        """Test redirecting non-existent URL"""
        response = client.get("/nonexistent", allow_redirects=False)
        assert response.status_code == 404
    
    def test_url_stats(self, client: TestClient):
        """Test getting URL statistics"""
        # Create a URL
        url_data = {"long_url": "https://www.stackoverflow.com"}
        create_response = client.post("/api/v1/urls/", json=url_data)
        short_code = create_response.json()["short_code"]
        
        # Access the URL to increment hits
        client.get(f"/{short_code}", allow_redirects=False)
        
        # Get stats
        response = client.get(f"/api/v1/urls/{short_code}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["short_code"] == short_code
        assert data["hits"] == 1  # Should be 1 after one redirect
    
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
        response = client.get(f"/{short_code}", allow_redirects=False)
        assert response.status_code == 404
    
    def test_invalid_url(self, client: TestClient):
        """Test creating URL with invalid URL"""
        url_data = {"long_url": "not-a-valid-url"}
        
        response = client.post("/api/v1/urls/", json=url_data)
        assert response.status_code == 422  # Validation error


class TestURLService:
    """Test URL service business logic"""
    
    def test_short_code_generation(self, client: TestClient):
        """Test that short codes are generated correctly"""
        url_data = {"long_url": "https://www.test.com"}
        
        response1 = client.post("/api/v1/urls/", json=url_data)
        response2 = client.post("/api/v1/urls/", json=url_data)
        
        # Both should succeed (different short codes for same URL)
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Short codes should be different
        assert data1["short_code"] != data2["short_code"]
        
        # Short codes should be 5 characters (as per config)
        assert len(data1["short_code"]) == 5
        assert len(data2["short_code"]) == 5
