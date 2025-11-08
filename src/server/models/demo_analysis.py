"""
Модель анализа демо
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database import Base


class DemoAnalysis(Base):
    __tablename__ = "demo_analyses"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    demo_id = Column(String, index=True)
    metadata = Column(JSON, nullable=True)
    overall_performance = Column(JSON, nullable=True)
    round_analysis = Column(JSON, nullable=True)
    key_moments = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    improvement_areas = Column(JSON, nullable=True)
    raw_data = Column(Text, nullable=True)  # Для хранения сырых данных демо
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="demo_analyses")
    
    def __repr__(self):
        return f"<DemoAnalysis(id={self.id}, demo_id={self.demo_id})>"

