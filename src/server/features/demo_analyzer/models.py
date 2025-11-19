from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class DemoMetadata(BaseModel):
    match_id: str
    map_name: str
    game_mode: str
    date_played: datetime
    duration: int
    score: Dict[str, int]


class PlayerPerformance(BaseModel):
    player_id: str
    kills: int
    deaths: int
    assists: int
    headshot_percentage: float
    entry_kills: int
    clutches_won: int
    damage_per_round: float
    utility_damage: float
    flash_assists: int


class RoundAnalysis(BaseModel):
    round_number: int
    winner_side: str
    winner_team: str
    round_type: str  # eco, force-buy, full-buy
    key_events: List[Dict]
    player_performances: Dict[str, PlayerPerformance]


class DemoAnalysis(BaseModel):
    demo_id: str
    metadata: DemoMetadata
    overall_performance: Dict[str, PlayerPerformance]
    round_analysis: List[RoundAnalysis]
    key_moments: List[Dict]
    recommendations: List[str]
    improvement_areas: List[Dict]
    coach_report: Optional[Dict] = None
