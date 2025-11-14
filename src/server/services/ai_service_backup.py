"""AI Service for player analysis"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class AIService:
    """AI analysis service with enhanced rule-based analysis"""

    def __init__(self):
        logger.info("AI Service initialized")
        self.translations = {
            "ru": {
                "elite": "элитный",
                "advanced": "продвинутый", 
                "intermediate": "средний",
                "beginner": "начинающий",
                "aiming": "прицеливание",
                "game_sense": "игровое мышление",
                "positioning": "позиционирование",
                "teamwork": "командная игра",
                "consistency": "стабильность",
                "advanced_tactics": "продвинутые тактики",
                "aim_training": "Тренировка aim_botz 30 минут в день",
                "demo_analysis": "Анализ демо профессиональных игроков",
                "tactics_improvement": "Совершенствование тактик",
                "time_estimate": "2-4 недели при регулярных тренировках"
            },
            "en": {
                "elite": "elite",
                "advanced": "advanced",
                "intermediate": "intermediate", 
                "beginner": "beginner",
                "aiming": "aiming",
                "game_sense": "game sense",
                "positioning": "positioning",
                "teamwork": "teamwork",
                "consistency": "consistency",
                "advanced_tactics": "advanced tactics",
                "aim_training": "Practice aim_botz 30 minutes daily",
                "demo_analysis": "Analyze professional player demos",
                "tactics_improvement": "Improve advanced tactics",
                "time_estimate": "2-4 weeks with regular practice"
            }
        }

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
        hs_pct = float(stats.get("headshot_percentage", 40.0))
        level = int(stats.get("level", 5))

        # Scoring system
        aim_score = min(10, max(1, int((kd * 3) + (hs_pct / 12))))
        game_sense_score = min(10, max(1, int(
            (win_rate / 8) + (level / 2)
        )))
        positioning_score = min(10, max(1, int(
            (win_rate / 10) + (kd * 2)
        )))

        # Analysis based on performance
        if kd >= 1.4 and win_rate >= 65:
            analysis_text = (
                f"{nickname} демонстрирует выдающийся уровень игры с K/D "
                f"{kd:.2f} и винрейтом {win_rate:.1f}%"
            )
            player_tier = "элитный"
        elif kd >= 1.2 and win_rate >= 55:
            analysis_text = (
                f"{nickname} показывает стабильные результаты с K/D {kd:.2f}"
            )
            player_tier = "продвинутый"
        else:
            analysis_text = f"{nickname} развивает навыки"
            player_tier = "средний"

        # Recommendations
        recommendations = []
        focus_areas = []

        if aim_score < 6:
            focus_areas.append("прицеливание")
            recommendations.append("Тренировка aim_botz 30 минут в день")

        if game_sense_score < 6:
            focus_areas.append("игровое мышление")
            recommendations.append("Анализ демо профессиональных игроков")

        if not focus_areas:
            focus_areas = ["продвинутые тактики"]
            recommendations = ["Совершенствование тактик"]

        return {
            "analysis": analysis_text,
            "player_tier": player_tier,
            "overall_score": int(
                (aim_score + game_sense_score + positioning_score) / 3
            ),
            "strengths": {
                "aim": aim_score,
                "game_sense": game_sense_score,
                "positioning": positioning_score
            },
            "focus_areas": focus_areas[:3],
            "recommendations": recommendations[:4],
            "estimated_improvement_time": (
                "2-4 недели при регулярных тренировках"
            )
        }
