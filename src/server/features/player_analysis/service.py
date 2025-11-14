"""
Player Analysis Service
Service for analyzing CS2 players on Faceit
"""
import logging
from typing import Optional, List, Dict
from datetime import datetime

from ...integrations.faceit_client import FaceitAPIClient
from ...services.ai_service import AIService
from ...services.cache_service import cache_service
from .schemas import (
    PlayerAnalysisResponse,
    PlayerStats,
    PlayerStrengths,
    PlayerWeaknesses,
    TrainingPlan
)

logger = logging.getLogger(__name__)


class PlayerAnalysisService:
    """Service for player analysis and statistics"""

    def __init__(self):
        self.faceit_client = FaceitAPIClient()
        self.ai_service = AIService()

    async def analyze_player(
        self,
        nickname: str
    ) -> Optional[PlayerAnalysisResponse]:
        """
        Complete player analysis

        Args:
            nickname: Player nickname

        Returns:
            Detailed analysis or None
        """
        try:
            # Check cache
            cache_key = cache_service.get_player_cache_key(
                nickname
            )
            cached = await cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache hit for player {nickname}")
                return PlayerAnalysisResponse(**cached)

            logger.info(
                f"Cache miss for player {nickname}, analyzing..."
            )
            # Fetch player data
            player = (
                await self.faceit_client.get_player_by_nickname(
                    nickname
                )
            )
            if not player:
                return None

            player_id = player.get("player_id")

            # Fetch statistics
            stats_data = (
                await self.faceit_client.get_player_stats(
                    player_id
                )
            )
            if not stats_data:
                return None

            # Parse statistics
            stats = self._parse_stats(stats_data, player)

            # Fetch match history for analysis
            match_history = (
                await self.faceit_client.get_match_history(
                    player_id,
                    limit=10
                )
            )

            # Use intelligent analysis
            ai_analysis = (
                await self.ai_service.analyze_player_with_ai(
                    nickname,
                    stats.dict(),
                    match_history
                )
            )

            # Parse analysis results
            strengths = PlayerStrengths(
                **ai_analysis["strengths"]
            )
            weaknesses = PlayerWeaknesses(
                **ai_analysis["weaknesses"]
            )
            training_plan = TrainingPlan(
                **ai_analysis["training_plan"]
            )
            overall_rating = ai_analysis["overall_rating"]

            result = PlayerAnalysisResponse(
                player_id=player_id,
                nickname=nickname,
                stats=stats,
                strengths=strengths,
                weaknesses=weaknesses,
                training_plan=training_plan,
                overall_rating=overall_rating,
                analyzed_at=datetime.utcnow()
            )

            # Save to cache (1 hour)
            await cache_service.set(
                cache_key,
                result.dict(),
                ttl=3600
            )

            return result

        except Exception:
            logger.exception(
                f"Error analyzing player {nickname}"
            )
            return None

    async def get_player_stats(
        self,
        nickname: str
    ) -> Optional[Dict]:
        """Get player statistics"""
        try:
            player = (
                await self.faceit_client.get_player_by_nickname(
                    nickname
                )
            )
            if not player:
                return None

            player_id = player.get("player_id")
            stats = (
                await self.faceit_client.get_player_stats(
                    player_id
                )
            )

            game_data = player.get("games", {}).get("cs2", {})
            return {
                "player_id": player_id,
                "nickname": nickname,
                "stats": stats,
                "level": game_data.get("skill_level"),
                "elo": game_data.get("faceit_elo")
            }
        except Exception:
            logger.exception(
                f"Error fetching stats for {nickname}"
            )
            return None

    async def get_player_matches(
        self,
        nickname: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get match history"""
        try:
            player = (
                await self.faceit_client.get_player_by_nickname(
                    nickname
                )
            )
            if not player:
                return []

            player_id = player.get("player_id")
            matches = (
                await self.faceit_client.get_match_history(
                    player_id,
                    limit=limit
                )
            )

            return matches
        except Exception:
            logger.exception(
                f"Error fetching matches for {nickname}"
            )
            return []

    async def search_players(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict]:
        """Search players"""
        try:
            players = (
                await self.faceit_client.search_players(
                    query,
                    limit=limit
                )
            )
            return players
        except Exception:
            logger.exception("Error searching players")
            return []

    def _parse_stats(
        self,
        stats_data: Dict,
        player: Dict
    ) -> PlayerStats:
        """Parse statistics from Faceit API"""
        lifetime = stats_data.get("lifetime", {})

        # Safe value extraction
        kd_ratio = float(
            lifetime.get(
                "Average K/D Ratio",
                lifetime.get("K/D Ratio", "1.0")
            )
        )
        win_rate = float(lifetime.get("Win Rate %", "50"))
        headshot_pct = float(
            lifetime.get(
                "Headshots %",
                lifetime.get("Average Headshots %", "40")
            )
        )
        avg_kills = float(
            lifetime.get(
                "Average Kills",
                lifetime.get("Kills", "15")
            )
        )
        matches = int(lifetime.get("Matches", "0"))

        # Data from player profile
        game_data = player.get("games", {}).get("cs2", {})
        elo = game_data.get("faceit_elo")
        level = game_data.get("skill_level")

        return PlayerStats(
            kd_ratio=kd_ratio,
            win_rate=win_rate,
            headshot_percentage=headshot_pct,
            average_kills=avg_kills,
            matches_played=matches,
            elo=elo,
            level=level
        )

    def _analyze_strengths(
        self,
        stats: PlayerStats
    ) -> PlayerStrengths:
        """Analyze player strengths based on statistics"""
        # Aim score based on K/D and headshot%
        aim_score = min(
            10,
            int(
                (stats.kd_ratio * 4) +
                (stats.headshot_percentage / 10)
            )
        )

        # Game sense score based on win rate
        game_sense_score = min(10, int(stats.win_rate / 10))

        # Positioning (basic evaluation)
        positioning_score = min(
            10,
            max(5, int(stats.win_rate / 12))
        )

        # Teamwork (evaluation based on win rate and match count)
        teamwork_score = min(
            10,
            int(
                (stats.win_rate / 10) +
                (min(stats.matches_played, 100) / 20)
            )
        )

        # Consistency (based on match count)
        consistency_score = min(
            10,
            int(min(stats.matches_played, 500) / 50)
        )

        return PlayerStrengths(
            aim=max(1, aim_score),
            game_sense=max(1, game_sense_score),
            positioning=max(1, positioning_score),
            teamwork=max(1, teamwork_score),
            consistency=max(1, consistency_score)
        )

    def _analyze_weaknesses(
        self,
        stats: PlayerStats
    ) -> PlayerWeaknesses:
        """Analyze player weaknesses"""
        weaknesses = []
        recommendations = []

        if stats.kd_ratio < 1.0:
            weaknesses.append("aim")
            recommendations.append(
                "Practice aiming on aim_botz and aim_training maps"
            )

        if stats.headshot_percentage < 40:
            weaknesses.append("headshot accuracy")
            recommendations.append(
                "Focus on headshot-only modes"
            )

        if stats.win_rate < 50:
            weaknesses.append("game sense")
            recommendations.append(
                "Study professional matches and strategies"
            )

        if stats.matches_played < 50:
            weaknesses.append("experience")
            recommendations.append(
                "Play more matches to gain experience"
            )

        # Determine priority area
        priority = weaknesses[0] if weaknesses else "consistency"

        if not weaknesses:
            weaknesses = ["consistency"]
            recommendations = ["Continue maintaining current skill level"]

        return PlayerWeaknesses(
            areas=weaknesses,
            priority=priority,
            recommendations=recommendations
        )

    def _generate_training_plan(
        self,
        weaknesses: PlayerWeaknesses
    ) -> TrainingPlan:
        """Generate training plan"""
        focus_areas = weaknesses.areas[:3]

        exercises = []

        if "aim" in focus_areas:
            exercises.append({
                "name": "Aim Training",
                "duration": "30 minutes",
                "description": "Aim training on aim_botz"
            })

        if "headshot accuracy" in focus_areas:
            exercises.append({
                "name": "Headshot Practice",
                "duration": "20 minutes",
                "description": "Headshot-only mode"
            })

        if "game sense" in focus_areas:
            exercises.append({
                "name": "Demo Review",
                "duration": "30 minutes",
                "description": "Watch and analyze professional matches"
            })

        if "experience" in focus_areas:
            exercises.append({
                "name": "Competitive Matches",
                "duration": "2-3 matches",
                "description": "Play competitive matches"
            })

        # If no specific exercises
        if not exercises:
            exercises.append({
                "name": "General Practice",
                "duration": "1 hour",
                "description": "General practice and skill maintenance"
            })

        return TrainingPlan(
            focus_areas=focus_areas,
            daily_exercises=exercises,
            estimated_time="2-4 weeks"
        )

    def _calculate_overall_rating(self, strengths: PlayerStrengths) -> int:
        """Calculate overall rating"""
        total = (
            strengths.aim +
            strengths.game_sense +
            strengths.positioning +
            strengths.teamwork +
            strengths.consistency
        )
        return min(10, max(1, int(total / 5)))
