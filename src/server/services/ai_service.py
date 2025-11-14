"""AI Service for player analysis"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class AIService:
    """AI analysis service with enhanced rule-based analysis"""

    def __init__(self):
        logger.info("AI Service initialized")

    async def analyze_player_with_ai(
        self,
        nickname: str,
        stats: Dict,
        match_history: List[Dict],
        language: str = "ru"
    ) -> Dict[str, any]:
        """Analyze player with enhanced rule-based analysis"""
        logger.info(f"Analyzing player {nickname}")
        return self._get_analysis(stats, nickname, language)

    def _get_analysis(
        self,
        stats: Dict,
        nickname: str = "Player",
        language: str = "ru"
    ) -> Dict:
        """Enhanced rule-based analysis"""
        kd = float(stats.get("kd_ratio", 1.0))
        win_rate = float(stats.get("win_rate", 50.0))
        level = int(stats.get("level", 5))

        # Scoring system
        aim_score = min(10, max(1, int(kd * 4)))
        game_sense_score = min(10, max(1, int(win_rate / 10)))

        # Analysis based on performance
        if language == "en":
            analysis_text = f"{nickname} shows K/D {kd:.2f}"
            tier = "intermediate"
            areas = ["aiming"]
            recs = ["Practice daily"]
            time_est = "2-4 weeks"
        else:
            analysis_text = f"{nickname} показывает K/D {kd:.2f}"
            tier = "средний"
            areas = ["прицеливание"]
            recs = ["Тренировка ежедневно"]
            time_est = "2-4 недели"

        return {
            "analysis": analysis_text,
            "player_tier": tier,
            "overall_score": int((aim_score + game_sense_score) / 2),
            "strengths": {"aim": aim_score},
            "focus_areas": areas,
            "recommendations": recs,
            "estimated_improvement_time": time_est
        }
