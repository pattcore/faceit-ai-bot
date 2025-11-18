"""
Groq Integration Service
Service for Groq AI models
"""
from typing import Dict, List, Optional
import logging
import aiohttp
import json
from ..config.settings import settings

logger = logging.getLogger(__name__)


class GroqService:
    """Service for Groq API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'GROQ_API_KEY', None)
        self.groq_base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = getattr(settings, "GROQ_MODEL", "llama-3.1-8b-instant")

        if not self.api_key:
            logger.warning("Groq API key not configured")

    async def analyze_player_performance(
        self,
        stats: Dict,
        match_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Analyze player performance with Groq AI

        Args:
            stats: Current player statistics
            match_history: Recent match history

        Returns:
            Detailed analysis and recommendations
        """
        if not self.api_key:
            return "Analysis unavailable - API key not configured"

        try:
            prompt = self._build_analysis_prompt(stats, match_history or [])

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional CS2 coach with "
                            "over 10 years of experience. Analyze "
                            "player statistics and provide specific, "
                            "actionable recommendations for improvement."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.groq_base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"][
                            "content"
                        ]
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Groq API error: {response.status} - "
                            f"{error_text}"
                        )
                        return (
                            f"Error analyzing performance: "
                            f"{response.status}"
                        )

        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            return (
                f"Error analyzing performance: {str(e)}"
            )

    async def generate_training_plan(
        self,
        player_stats: Dict,
        focus_areas: List[str]
    ) -> Dict:
        """
        Generate personalized training plan

        Args:
            player_stats: Player statistics
            focus_areas: Areas for improvement

        Returns:
            Structured training plan
        """
        if not self.api_key:
            return self._get_default_training_plan()

        try:
            prompt = f"""
            Create a detailed training plan for a CS2 player.

            Statistics:
            - K/D: {player_stats.get('kd_ratio', 'N/A')}
            - Headshot %: {player_stats.get('hs_percentage', 'N/A')}
            - Win Rate: {player_stats.get('win_rate', 'N/A')}

            Focus on: {', '.join(focus_areas)}

            Return ONLY a valid JSON object with fields:
            - daily_exercises: list of objects with fields name, duration, description
            - weekly_goals: list of strings
            - estimated_time: string
            Do not add any explanations, comments or markdown, only pure JSON.
            """

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a CS2 coach. "
                            "Reply only in JSON format."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 1000
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.groq_base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"][
                            "content"
                        ]

                        # Try to parse JSON strictly first
                        text = content.strip()

                        # Remove optional markdown code fences
                        if text.startswith("```"):
                            lines = text.splitlines()
                            cleaned_lines = [
                                line
                                for line in lines
                                if not line.strip().startswith("```")
                            ]
                            text = "\n".join(cleaned_lines).strip()

                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            # Try to extract the first JSON object from the text
                            start = text.find("{")
                            end = text.rfind("}")
                            if start != -1 and end != -1 and end > start:
                                try:
                                    return json.loads(text[start : end + 1])
                                except json.JSONDecodeError:
                                    logger.error(
                                        "Failed to parse Groq training plan JSON",
                                        exc_info=True,
                                    )
                            return self._get_default_training_plan()
                    else:
                        return self._get_default_training_plan()

        except Exception as e:
            logger.error(f"Error generating training plan: {str(e)}")
            return self._get_default_training_plan()

    def _build_analysis_prompt(
        self,
        stats: Dict,
        match_history: List[Dict]
    ) -> str:
        """Build analysis prompt"""
        return f"""
        Analyze CS2 player statistics:

        Current metrics:
        - K/D Ratio: {stats.get('kd_ratio', 'N/A')}
        - Headshot %: {stats.get('hs_percentage', 'N/A')}
        - Win Rate: {stats.get('win_rate', 'N/A')}
        - Avg Damage: {stats.get('avg_damage', 'N/A')}
        - Matches Played: {stats.get('matches_played', 'N/A')}

        Recent match history: {len(match_history)} matches

        Provide detailed analysis:
        1. Strengths
        2. Weaknesses
        3. Specific recommendations for improvement
        4. Action plan for the next week
        """

    def _get_default_training_plan(self) -> Dict:
        """Default training plan"""
        return {
            "daily_exercises": [
                {
                    "name": "Aim Training",
                    "duration": 30,
                    "description": "Aim training on aim_botz"
                },
                {
                    "name": "Spray Control",
                    "duration": 20,
                    "description": "Recoil control for AK-47 and M4A4"
                }
            ],
            "weekly_goals": [
                "Increase accuracy by 5%",
                "Improve K/D to 1.2"
            ],
            "estimated_time": "2-3 weeks"
        }
