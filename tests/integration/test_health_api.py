"""
Integration тесты для health check endpoints
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestHealthAPI:
    """Тесты для health check API"""
    
    def test_root_endpoint(self, client):
        """Тест корневого endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "message" in data
    
    def test_health_endpoint(self, client):
        """Тест health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data

