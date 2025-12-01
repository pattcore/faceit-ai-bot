from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class PlayerStats(BaseModel):
    faceit_elo: int
    matches_played: int
    win_rate: float
    avg_kd: float
    avg_hs: float
    favorite_maps: List[str]
    last_20_matches: List[Dict]

class TeammatePreferences(BaseModel):
    min_elo: int
    max_elo: int
    preferred_maps: List[str]
    preferred_roles: List[str]
    communication_lang: List[str]
    play_style: str
    time_zone: str
    about: Optional[str] = None
    availability: Optional[str] = None
    discord_contact: Optional[str] = None
    telegram_contact: Optional[str] = None
    contact_url: Optional[str] = None

class TeammateProfile(BaseModel):
    user_id: str
    faceit_nickname: str
    stats: PlayerStats
    preferences: TeammatePreferences
    availability: List[str]
    team_history: List[Dict]
    about: Optional[str] = None
    discord_contact: Optional[str] = None
    telegram_contact: Optional[str] = None
    contact_url: Optional[str] = None
    compatibility_score: Optional[float] = None
    match_summary: Optional[str] = None
