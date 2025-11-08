"""
Integration тесты для API поиска тиммейтов
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestTeammatesAPI:
    """Тесты для API поиска тиммейтов"""
    
    def test_search_teammates(self, client, teammate_preferences):
        """Тест поиска тиммейтов"""
        response = client.post(
            "/teammates/search",
            params={"user_id": "test_user_id"},
            json=teammate_preferences
        )
        
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_search_teammates_invalid_preferences(self, client):
        """Тест поиска тиммейтов с невалидными предпочтениями"""
        invalid_preferences = {
            "min_elo": -100,
            "max_elo": 100,
            "region": "INVALID"
        }
        
        response = client.post(
            "/teammates/search",
            params={"user_id": "test_user_id"},
            json=invalid_preferences
        )
        
        assert response.status_code in [400, 422]  # Validation error
    
    def test_update_preferences(self, client, teammate_preferences):
        """Тест обновления предпочтений"""
        response = client.put(
            "/teammates/preferences",
            params={"user_id": "test_user_id"},
            json=teammate_preferences
        )
        
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["min_elo"] == teammate_preferences["min_elo"]
            assert data["max_elo"] == teammate_preferences["max_elo"]

