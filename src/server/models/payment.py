"""
Model payments
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import sys
from pathlib import Path
import enum

sys.path.append(str(Path(__file__).parent.parent))
from database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentProvider(str, enum.Enum):
    YOOKASSA = "YOOKASSA"
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    SBP = "SBP"
    QIWI = "QIWI"
    CRYPTO = "CRYPTO"


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    payment_id = Column(String, unique=True, index=True)  # ID от платежного провайдера
    provider = Column(SQLEnum(PaymentProvider), index=True)
    amount = Column(Float)
    currency = Column(String, default="RUB")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    description = Column(String, nullable=True)
    payment_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"
