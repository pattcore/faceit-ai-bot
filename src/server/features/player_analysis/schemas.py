"""
Player Analysis Schemas
Схемы данных для анализа игроков
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class PlayerStats(BaseModel):
    """Статистика игрока"""
    kd_ratio: float = Field(..., description="K/D соотношение")
    win_rate: float = Field(..., description="Процент побед")
    headshot_percentage: float = Field(..., description="Процент хедшотов")
    average_kills: float = Field(..., description="Среднее количество убийств")
    matches_played: int = Field(..., description="Сыграно матчей")
    elo: Optional[int] = Field(None, description="ELO рейтинг")
    level: Optional[int] = Field(None, description="Уровень на Faceit")


class PlayerStrengths(BaseModel):
    """Сильные стороны игрока"""
    aim: int = Field(..., ge=1, le=10, description="Оценка прицеливания")
    game_sense: int = Field(..., ge=1, le=10, description="Игровое чутье")
    positioning: int = Field(..., ge=1, le=10, description="Позиционирование")
    teamwork: int = Field(..., ge=1, le=10, description="Командная игра")
    consistency: int = Field(..., ge=1, le=10, description="Стабильность")


class PlayerWeaknesses(BaseModel):
    """Слабые стороны игрока"""
    areas: List[str] = Field(..., description="Области для улучшения")
    priority: str = Field(..., description="Приоритетная область")
    recommendations: List[str] = Field(..., description="Рекомендации")


class TrainingPlan(BaseModel):
    """План тренировок"""
    focus_areas: List[str] = Field(..., description="Области фокуса")
    daily_exercises: List[Dict[str, str]] = Field(..., description="Ежедневные упражнения")
    estimated_time: str = Field(..., description="Примерное время улучшения")


class PlayerAnalysisRequest(BaseModel):
    """Запрос на анализ игрока"""
    nickname: str = Field(..., min_length=3, max_length=50, description="Никнейм игрока")
    detailed: bool = Field(default=True, description="Детальный анализ")


class PlayerAnalysisResponse(BaseModel):
    """Ответ с анализом игрока"""
    player_id: str = Field(..., description="ID игрока")
    nickname: str = Field(..., description="Никнейм")
    stats: PlayerStats = Field(..., description="Статистика")
    strengths: PlayerStrengths = Field(..., description="Сильные стороны")
    weaknesses: PlayerWeaknesses = Field(..., description="Слабые стороны")
    training_plan: TrainingPlan = Field(..., description="План тренировок")
    overall_rating: int = Field(..., ge=1, le=10, description="Общая оценка")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Время анализа")
    
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
                        "Практиковать удержание позиций",
                        "Изучить карты детальнее"
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
