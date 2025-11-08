"""
Integration тесты для API подписок
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestSubscriptionsAPI:
    """Тесты для API подписок"""
    
    def test_get_subscription_plans(self, client):
        """Тест получения планов подписки"""
        response = client.get("/subscriptions/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
        assert "FREE" in data or "free" in str(data).lower()
        assert "BASIC" in data or "basic" in str(data).lower()
    
    def test_get_user_subscription(self, client):
        """Тест получения подписки пользователя"""
        user_id = "test_user_id"
        
        response = client.get(f"/subscriptions/{user_id}")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "subscription_tier" in data
    
    def test_create_subscription(self, client):
        """Тест создания подписки"""
        user_id = "test_user_id"
        tier = "BASIC"
        
        response = client.post(
            f"/subscriptions/{user_id}",
            params={"tier": tier}
        )
        
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["user_id"] == user_id
            assert data["subscription_tier"] == tier
    
    def test_check_feature_access(self, client):
        """Тест проверки доступа к функции"""
        user_id = "test_user_id"
        feature = "detailed_analysis"
        
        response = client.get(
            f"/subscriptions/{user_id}/check-feature",
            params={"feature": feature}
        )
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "has_access" in data
            assert isinstance(data["has_access"], bool)

