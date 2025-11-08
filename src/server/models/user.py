"""
Модель пользователя
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    faceit_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

