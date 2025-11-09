from typing import Optional, Dict
from fastapi import HTTPException
from .models import SubscriptionTier
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.subscription_plans = {
            SubscriptionTier.FREE: {
                'price': 0.0,
                'demos_per_month': 2,
                'features': {
                    'detailed_analysis': False,
                    'teammate_search': False,
                    'custom_recommendations': False,
                    'priority_support': False,
                    'ai_coach': False,
                    'team_analysis': False
                }
            },
            SubscriptionTier.BASIC: {
                'price': 9.99,
                'demos_per_month': 10,
                'features': {
                    'detailed_analysis': True,
                    'teammate_search': True,
                    'custom_recommendations': False,
                    'priority_support': False,
                    'ai_coach': False,
                    'team_analysis': False
                }
            },
            SubscriptionTier.PRO: {
                'price': 19.99,
                'demos_per_month': 30,
                'features': {
                    'detailed_analysis': True,
                    'teammate_search': True,
                    'custom_recommendations': True,
                    'priority_support': True,
                    'ai_coach': False,
                    'team_analysis': True
                }
            },
            SubscriptionTier.ELITE: {
                'price': 39.99,
                'demos_per_month': -1,  # Unlimited
                'features': {
                    'detailed_analysis': True,
                    'teammate_search': True,
                    'custom_recommendations': True,
                    'priority_support': True,
                    'ai_coach': True,
                    'team_analysis': True
                }
            }
        }

    async def get_subscription_plans(self) -> Dict[str, Subscription]:
        """Получение информации о доступных планах подписки"""
        try:
            return {
                tier.value: Subscription(
                    tier=tier,
                    price=plan['price'],
                    features=plan['features'],
                    description=self._get_plan_description(tier)
                )
                for tier, plan in self.subscription_plans.items()
            }
        except Exception as e:
            logger.exception("Failed to get subscription plans")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get subscription plans: {str(e)}"
            )

    async def get_user_subscription(self, user_id: str) -> Optional[UserSubscription]:
        """Получение информации о подписке пользователя"""
        try:
            # Database query not implemented
            return UserSubscription(
                user_id=user_id,
                subscription_tier=SubscriptionTier.FREE,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                is_active=True,
                demos_remaining=2
            )
        except Exception as e:
            logger.exception(f"Failed to get subscription for user {user_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get user subscription: {str(e)}"
            )

    async def create_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier
    ) -> UserSubscription:
        """Создание новой подписки"""
        try:
            plan = self.subscription_plans[tier]
            subscription = UserSubscription(
                user_id=user_id,
                subscription_tier=tier,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                is_active=True,
                demos_remaining=plan['demos_per_month']
            )
            # Database save not implemented
            return subscription
        except Exception as e:
            logger.exception(f"Failed to create subscription for user {user_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create subscription: {str(e)}"
            )

    async def check_feature_access(
        self,
        user_id: str,
        feature: str
    ) -> bool:
        """Check feature access"""
        try:
            subscription = await self.get_user_subscription(user_id)
            plan = self.subscription_plans[subscription.subscription_tier]
            return plan['features'].get(feature, False)
        except Exception as e:
            logger.exception(f"Failed to check feature access for user {user_id}")
            return False

    def _get_plan_description(self, tier: SubscriptionTier) -> str:
        """Получение описания плана подписки"""
        descriptions = {
            SubscriptionTier.FREE: "Базовый анализ демок и ограниченный функционал",
            SubscriptionTier.BASIC: "Расширенный анализ и поиск тиммейтов",
            SubscriptionTier.PRO: "Полный анализ, приоритетная поддержка и командный анализ",
            SubscriptionTier.ELITE: "Безлимитный доступ ко всем функциям и персональный AI-коуч"
        }
        return descriptions.get(tier, "")