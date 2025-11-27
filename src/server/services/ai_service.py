"""AI Service for player analysis"""
import logging
from typing import Dict, List, Any

from ..ai.groq_service import GroqService

logger = logging.getLogger(__name__)


class AIService:
    """AI analysis service with enhanced rule-based analysis"""

    def __init__(self):
        self.groq_service = GroqService()
        logger.info("AI Service initialized")

    async def analyze_player_with_ai(
        self,
        nickname: str,
        stats: Dict,
        match_history: List[Dict],
        language: str = "ru"
    ) -> Dict[str, Any]:
        """Analyze player with Groq-backed analysis and structured output"""
        logger.info(f"Analyzing player {nickname}")

        kd = float(stats.get("kd_ratio", 1.0))
        win_rate = float(stats.get("win_rate", 50.0))
        hs_pct = float(
            stats.get(
                "headshot_percentage",
                stats.get("hs_percentage", 40.0),
            )
        )
        matches = int(stats.get("matches_played", stats.get("matches", 0)))

        avg_damage = stats.get("avg_damage")
        if avg_damage is None:
            avg_damage = stats.get("average_damage", stats.get("average_kills"))

        groq_stats = {
            "kd_ratio": kd,
            "win_rate": win_rate,
            "hs_percentage": hs_pct,
            "matches_played": matches,
            "avg_damage": avg_damage if avg_damage is not None else "N/A",
        }

        detailed_analysis = await self.groq_service.analyze_player_performance(
            stats=groq_stats,
            match_history=match_history,
            language=language,
        )

        aim_score = min(10, int((kd * 4) + (hs_pct / 10)))
        game_sense_score = min(10, int(win_rate / 10))
        positioning_score = min(10, max(5, int(win_rate / 12)))
        teamwork_score = min(10, int((win_rate / 10) + (min(matches, 100) / 20)))
        consistency_score = min(10, int(min(matches, 500) / 50))

        strengths = {
            "aim": max(1, aim_score),
            "game_sense": max(1, game_sense_score),
            "positioning": max(1, positioning_score),
            "teamwork": max(1, teamwork_score),
            "consistency": max(1, consistency_score),
        }

        weaknesses_areas: List[str] = []
        weaknesses_recs: List[str] = []

        if kd < 1.0:
            weaknesses_areas.append("aim")
            weaknesses_recs.append("Больше тренируй аим на тренировочных картах")

        if hs_pct < 40:
            weaknesses_areas.append("headshot accuracy")
            weaknesses_recs.append("Сфокусируйся на режимах с упором на хедшоты")

        if win_rate < 50:
            weaknesses_areas.append("game sense")
            weaknesses_recs.append(
                "Смотри демки и стримы сильных игроков, разбирай их решения"
            )

        if matches < 50:
            weaknesses_areas.append("experience")
            weaknesses_recs.append("Играй больше рейтинговых матчей для набора опыта")

        if not weaknesses_areas:
            weaknesses_areas = ["consistency"]
            weaknesses_recs = ["Поддерживай текущий уровень игры и стабильность"]

        # Enrich recommendations with AI-generated suggestions
        ai_recs = self._extract_ai_recommendations(
            detailed_analysis,
            language=language,
        )
        if ai_recs:
            for rec in ai_recs:
                if rec not in weaknesses_recs:
                    weaknesses_recs.append(rec)
                    if len(weaknesses_recs) >= 10:
                        break

        priority = weaknesses_areas[0]

        weaknesses = {
            "areas": weaknesses_areas,
            "priority": priority,
            "recommendations": weaknesses_recs,
        }

        training_plan = await self.generate_training_plan(
            nickname=nickname,
            stats=stats,
            language=language,
            focus_areas=weaknesses_areas,
        )

        overall_rating = int(
            min(
                10,
                max(
                    1,
                    (
                        aim_score
                        + game_sense_score
                        + positioning_score
                        + teamwork_score
                        + consistency_score
                    )
                    / 5,
                ),
            )
        )

        return {
            "detailed_analysis": detailed_analysis,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "training_plan": training_plan,
            "overall_rating": overall_rating,
        }

    async def generate_training_plan(
        self,
        nickname: str,
        stats: Dict,
        language: str = "ru",
        focus_areas: List[str] | None = None,
    ) -> Dict[str, Any]:
        """Generate personalized training plan for player"""
        kd = float(stats.get("kd_ratio", 1.0))
        win_rate = float(stats.get("win_rate", 50.0))
        hs_pct = float(stats.get("hs_percentage", 40.0))

        if focus_areas is None:
            focus_areas = []
            if kd < 1.1:
                focus_areas.append("aim")
            if win_rate < 55:
                focus_areas.append("game sense")
            if not focus_areas:
                focus_areas.append("consistency")

        # Try to get structured training plan from Groq
        player_stats = {
            "kd_ratio": kd,
            "win_rate": win_rate,
            "hs_percentage": hs_pct,
        }

        plan_data = await self.groq_service.generate_training_plan(
            player_stats=player_stats,
            focus_areas=focus_areas,
            language=language,
        )

        daily_exercises_raw = plan_data.get("daily_exercises", [])
        daily_exercises: List[Dict[str, Any]] = []

        for ex in daily_exercises_raw:
            if not isinstance(ex, dict):
                continue
            name = str(ex.get("name") or "Training exercise")
            duration_val = ex.get("duration")
            if isinstance(duration_val, (int, float)):
                duration = f"{int(duration_val)} min"
            elif duration_val:
                duration = str(duration_val)
            else:
                duration = "30 min"
            description = str(ex.get("description") or "")
            daily_exercises.append(
                {
                    "name": name,
                    "duration": duration,
                    "description": description,
                }
            )

        estimated_time_raw = plan_data.get("estimated_time")
        if estimated_time_raw:
            estimated_time = str(estimated_time_raw)
        else:
            estimated_time = "4 weeks" if language == "en" else "4 недели"

        # Heuristic validation: if the AI returned an obviously non-CS2 or
        # malformed plan (fitness, skiing, non-Russian/CJK, etc.),
        # treat it as invalid so that we fall back to the static CS2 plan below.
        invalid_plan = False

        # Collect all text fields for inspection
        text_parts: List[str] = []
        for ex in daily_exercises:
            if isinstance(ex, dict):
                text_parts.append(str(ex.get("name", "")))
                text_parts.append(str(ex.get("description", "")))
        text_parts.append(estimated_time)
        all_text = " ".join(text_parts).strip()

        def _contains_cjk(s: str) -> bool:
            for ch in s:
                if "\u4e00" <= ch <= "\u9fff":
                    return True
            return False

        if all_text and _contains_cjk(all_text):
            invalid_plan = True

        lowered = all_text.lower()
        banned_keywords = [
            "warm-up",
            "warm up",
            "cardio",
            "yoga",
            "meditation",
            "stretch",
            "stretching",
            "mobility",
            "ski",
            "skiing",
            "walking",
            "walk ",
            "running",
            "run ",
            "jogging",
            "jog ",
        ]
        if any(bad in lowered for bad in banned_keywords):
            invalid_plan = True

        if invalid_plan:
            daily_exercises = []

        # Fallback to previous static plan if AI did not provide anything useful
        if not daily_exercises:
            if language == "en":
                daily_exercises = [
                    {
                        "name": "Aim training",
                        "duration": "30 min",
                        "description": "Aim routine on aim_botz and training maps",
                    },
                    {
                        "name": "Demo review",
                        "duration": "30 min",
                        "description": "Watch and analyze your recent matches",
                    },
                    {
                        "name": "Competitive matches",
                        "duration": "2-3 matches",
                        "description": "Play 2-3 ranked matches focusing on mistakes",
                    },
                ]
                estimated_time = "4 weeks"
            else:
                daily_exercises = [
                    {
                        "name": "Тренировка аима",
                        "duration": "30 мин",
                        "description": "Рутина на aim_botz и тренировочных картах",
                    },
                    {
                        "name": "Разбор демо",
                        "duration": "30 мин",
                        "description": "Смотреть и разбирать свои последние матчи",
                    },
                    {
                        "name": "Соревновательные матчи",
                        "duration": "2-3 матча",
                        "description": "Играть 2-3 рейтинговых матча с фокусом на ошибках",
                    },
                ]
                estimated_time = "4 недели"

        return {
            "focus_areas": focus_areas,
            "daily_exercises": daily_exercises,
            "estimated_time": estimated_time,
        }

    def _extract_ai_recommendations(
        self,
        detailed_text: str,
        language: str = "ru",
    ) -> List[str]:
        """Extract and sanitize bullet-style recommendations from AI analysis text."""
        recommendations: List[str] = []

        # Normalize language to a small set
        lang = str(language or "ru").lower()
        if lang.startswith("en"):
            lang = "en"
        elif lang.startswith("ru"):
            lang = "ru"
        else:
            lang = "en"

        def _contains_cjk(s: str) -> bool:
            for ch in s:
                if "\u4e00" <= ch <= "\u9fff":
                    return True
            return False

        def _contains_cyrillic(s: str) -> bool:
            for ch in s:
                if "а" <= ch <= "я" or "А" <= ch <= "Я":
                    return True
            return False

        # Phrases that look like generic / template garbage rather than
        # concrete CS2 coaching tips.
        banned_substrings = [
            "модульный анализ",
            "силовые методы",
            "контрольные рекомендации",
            "влияние на ее игроков",
            "влияние на её игроков",
            "влияние на ее игру",
            "влияние на её игру",
        ]

        try:
            for raw_line in detailed_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                # We only consider bullet-style or numbered lines
                if not (
                    line[0].isdigit()
                    or line.startswith(("-", "•", "*"))
                ):
                    continue

                clean_line = line.lstrip("-•*0123456789. ").strip()
                if not clean_line:
                    continue

                # Drop too short / meaningless fragments
                if len(clean_line) < 10:
                    continue

                # Remove lines with obvious non-target language content
                if _contains_cjk(clean_line):
                    continue

                lower = clean_line.lower()
                if any(bad in lower for bad in banned_substrings):
                    continue

                # For Russian we expect at least some Cyrillic characters,
                # иначе это, скорее всего, мусор или общее описание.
                if lang == "ru" and not _contains_cyrillic(clean_line):
                    continue

                recommendations.append(clean_line)

                # Защитный лимит на количество AI-рекомендаций
                if len(recommendations) >= 10:
                    break
        except Exception:
            logger.exception(
                "Failed to parse AI recommendations from detailed analysis",
            )

        return recommendations
