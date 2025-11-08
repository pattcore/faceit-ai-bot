from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Optional
from ..subscriptions.service import SubscriptionService
from ..subscriptions.models import Subscription, UserSubscription, SubscriptionTier
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

subscription_service = SubscriptionService()

@router.get("/plans", response_model=Dict[str, Subscription])
async def get_subscription_plans():
    """
    Получение информации о доступных планах подписки
    """
    return await subscription_service.get_subscription_plans()

@router.get("/{user_id}", response_model=Optional[UserSubscription])
async def get_user_subscription(user_id: str):
    """
    Получение информации о текущей подписке пользователя
    """
    return await subscription_service.get_user_subscription(user_id)

@router.post("/{user_id}", response_model=UserSubscription)
async def create_subscription(user_id: str, tier: SubscriptionTier):
    """
    Создание новой подписки для пользователя
    """
    return await subscription_service.create_subscription(user_id, tier)

@router.get("/{user_id}/check-feature")
async def check_feature_access(user_id: str, feature: str):
    """
    Check feature access for user
    """
    has_access = await subscription_service.check_feature_access(user_id, feature)
    return {"has_access": has_access}