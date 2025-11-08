"""
Модели подписок
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String, primary_key=True, index=True)
    tier = Column(String, unique=True, index=True)  # FREE, BASIC, PRO, ELITE
    price = Column(Float, default=0.0)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Subscription(tier={self.tier}, price={self.price})>"


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    subscription_tier = Column(String, index=True)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    demos_remaining = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="subscriptions")
    
    def __repr__(self):
        return f"<UserSubscription(user_id={self.user_id}, tier={self.subscription_tier}, active={self.is_active})>"

