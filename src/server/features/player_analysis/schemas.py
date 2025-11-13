"""
Player Analysis Schemas
Data schemas for player analysis
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class PlayerStats(BaseModel):
    """Player statistics"""
    kd_ratio: float = Field(..., description="K/D ratio")
    win_rate: float = Field(..., description="Win rate percentage")
    headshot_percentage: float = Field(..., description="Headshot percentage")
    average_kills: float = Field(..., description="Average kills")
    matches_played: int = Field(..., description="Matches played")
    elo: Optional[int] = Field(None, description="ELO rating")
    level: Optional[int] = Field(None, description="Faceit level")


class PlayerStrengths(BaseModel):
    """Player strengths"""
    aim: int = Field(..., ge=1, le=10, description="Aim rating")
    game_sense: int = Field(..., ge=1, le=10, description="Game sense")
    positioning: int = Field(..., ge=1, le=10, description="Positioning")
    teamwork: int = Field(..., ge=1, le=10, description="Teamwork")
    consistency: int = Field(..., ge=1, le=10, description="Consistency")


class PlayerWeaknesses(BaseModel):
    """Player weaknesses"""
    areas: List[str] = Field(..., description="Areas for improvement")
    priority: str = Field(..., description="Priority area")
    recommendations: List[str] = Field(..., description="Recommendations")


class TrainingPlan(BaseModel):
    """Training plan"""
    focus_areas: List[str] = Field(..., description="Focus areas")
    daily_exercises: List[Dict[str, str]] = Field(
        ..., description="Daily exercises"
    )
    estimated_time: str = Field(..., description="Estimated improvement time")


class PlayerAnalysisRequest(BaseModel):
    """Player analysis request"""
    nickname: str = Field(
        ..., min_length=3, max_length=50, description="Player nickname"
    )
    detailed: bool = Field(default=True, description="Detailed analysis")


class PlayerAnalysisResponse(BaseModel):
    """Player analysis response"""
    player_id: str = Field(..., description="Player ID")
    nickname: str = Field(..., description="Nickname")
    stats: PlayerStats = Field(..., description="Statistics")
    strengths: PlayerStrengths = Field(..., description="Strengths")
    weaknesses: PlayerWeaknesses = Field(..., description="Weaknesses")
    training_plan: TrainingPlan = Field(..., description="Training plan")
    overall_rating: int = Field(..., ge=1, le=10, description="Overall rating")
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Analysis time"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "abc123",
                "nickname": "ProPlayer",
                "stats": {
                    "kd_ratio": 1.25,
                    "win_rate": 55.5,
                    "headshot_percentage": 48.2,
                    "average_kills": 18.5,
                    "matches_played": 250,
                    "elo": 2100,
                    "level": 8
                },
                "strengths": {
                    "aim": 8,
                    "game_sense": 7,
                    "positioning": 6,
                    "teamwork": 7,
                    "consistency": 8
                },
                "weaknesses": {
                    "areas": ["positioning", "economy management"],
                    "priority": "positioning",
                    "recommendations": [
                        "Practice holding positions",
                        "Study maps in detail"
                    ]
                },
                "training_plan": {
                    "focus_areas": ["positioning", "map knowledge"],
                    "daily_exercises": [
                        {"name": "Position practice", "duration": "30 min"}
                    ],
                    "estimated_time": "2-3 weeks"
                },
                "overall_rating": 7,
                "analyzed_at": "2025-11-09T18:00:00Z"
            }
        }
