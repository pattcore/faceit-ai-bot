"""
Unit тесты для сервиса подписок
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.server.features.subscriptions.service import SubscriptionService
from src.server.features.subscriptions.models import SubscriptionTier


@pytest.mark.unit
class TestSubscriptionService:
    """Тесты для SubscriptionService"""
    
    @pytest.fixture
    def subscription_service(self):
        """Создание сервиса подписок"""
        return SubscriptionService()
    
    @pytest.mark.asyncio
    async def test_get_subscription_plans(self, subscription_service):
        """Тест получения планов подписки"""
        plans = await subscription_service.get_subscription_plans()
        
        assert plans is not None
        assert isinstance(plans, dict)
        assert SubscriptionTier.FREE.value in plans
        assert SubscriptionTier.BASIC.value in plans
        assert SubscriptionTier.PRO.value in plans
        assert SubscriptionTier.ELITE.value in plans
    
    @pytest.mark.asyncio
    async def test_get_subscription_plans_structure(self, subscription_service):
        """Тест структуры планов подписки"""
        plans = await subscription_service.get_subscription_plans()
        
        free_plan = plans[SubscriptionTier.FREE.value]
        assert free_plan.price == 0.0
        assert free_plan.tier == SubscriptionTier.FREE
        
        basic_plan = plans[SubscriptionTier.BASIC.value]
        assert basic_plan.price == 9.99
        assert basic_plan.tier == SubscriptionTier.BASIC
        
        pro_plan = plans[SubscriptionTier.PRO.value]
        assert pro_plan.price == 19.99
        assert pro_plan.tier == SubscriptionTier.PRO
    
    @pytest.mark.asyncio
    async def test_get_user_subscription(self, subscription_service):
        """Тест получения подписки пользователя"""
        user_id = "test_user_id"
        subscription = await subscription_service.get_user_subscription(user_id)
        
        assert subscription is not None
        assert subscription.user_id == user_id
        assert subscription.subscription_tier == SubscriptionTier.FREE
        assert subscription.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_subscription(self, subscription_service):
        """Тест создания подписки"""
        user_id = "test_user_id"
        tier = SubscriptionTier.BASIC
        
        subscription = await subscription_service.create_subscription(user_id, tier)
        
        assert subscription is not None
        assert subscription.user_id == user_id
        assert subscription.subscription_tier == tier
        assert subscription.is_active is True
        assert subscription.demos_remaining == 10
    
    @pytest.mark.asyncio
    async def test_create_subscription_elite(self, subscription_service):
        """Тест создания Elite подписки"""
        user_id = "test_user_id"
        tier = SubscriptionTier.ELITE
        
        subscription = await subscription_service.create_subscription(user_id, tier)
        
        assert subscription is not None
        assert subscription.subscription_tier == tier
        assert subscription.demos_remaining == -1  # Unlimited
    
    @pytest.mark.asyncio
    async def test_check_feature_access_free(self, subscription_service):
        """Тест проверки доступа к функциям для FREE подписки"""
        user_id = "test_user_id"
        
        # FREE subscription should not have access to paid features
        has_access = await subscription_service.check_feature_access(user_id, "detailed_analysis")
        assert has_access is False
        
        has_access = await subscription_service.check_feature_access(user_id, "teammate_search")
        assert has_access is False
    
    @pytest.mark.asyncio
    async def test_check_feature_access_basic(self, subscription_service):
        """Тест проверки доступа к функциям для BASIC подписки"""
        user_id = "test_user_id"
        await subscription_service.create_subscription(user_id, SubscriptionTier.BASIC)
        
        # BASIC subscription should have access to basic features
        has_access = await subscription_service.check_feature_access(user_id, "detailed_analysis")
        assert has_access is True
        
        has_access = await subscription_service.check_feature_access(user_id, "teammate_search")
        assert has_access is True
        
        # But not to premium features
        has_access = await subscription_service.check_feature_access(user_id, "ai_coach")
        assert has_access is False

