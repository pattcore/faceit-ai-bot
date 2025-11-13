"""
AI Analysis API Routes - Simple working version
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai-analysis"])


class PlayerAnalysisRequest(BaseModel):
    """Player analysis request"""
    player_nickname: str
    faceit_id: str | None = None


class PlayerAnalysisResponse(BaseModel):
    """Player analysis response"""
    player_id: str
    nickname: str
    analysis: str
    recommendations: List[str]
    training_plan: Dict
    strengths: List[str]
    weaknesses: List[str]


@router.post("/analyze-player", response_model=PlayerAnalysisResponse)
async def analyze_player(request: PlayerAnalysisRequest):
    """
    Simple player analysis based on Faceit statistics
    """
    try:
        from ...integrations.faceit_client import FaceitAPIClient

        # Initialize Faceit client
        faceit_client = FaceitAPIClient()

        # Fetch player data
        if request.faceit_id:
            player_data = await faceit_client.get_player_by_id(
                request.faceit_id
            )
            player_id = request.faceit_id
        else:
            player_data = await faceit_client.get_player_by_nickname(
                request.player_nickname
            )
            if not player_data:
                raise HTTPException(
                    status_code=404, detail="Player not found"
                )
            player_id = player_data['player_id']

        # Fetch stats
        stats = await faceit_client.get_player_stats(player_id)
        if not stats:
            raise HTTPException(
                status_code=404, detail="Stats not available"
            )

        # Extract key metrics
        lifetime_stats = stats.get('lifetime', {})
        kd_ratio = float(lifetime_stats.get('K/D Ratio', '1.0'))
        win_rate = float(lifetime_stats.get('Win Rate %', '50'))

        # Simple analysis based on stats
        if kd_ratio >= 1.5:
            analysis = (
                f"Excellent player with K/D {kd_ratio:.2f} "
                f"and win rate {win_rate:.1f}%"
            )
            strengths = ["aim", "game_sense", "positioning"]
            weaknesses = ["consistency"]
            recommendations = [
                "Maintain current performance", 
                "Focus on team coordination"
            ]
        elif kd_ratio >= 1.2:
            analysis = (
                f"Good player with K/D {kd_ratio:.2f} "
                f"and win rate {win_rate:.1f}%"
            )
            strengths = ["aim", "game_sense"]
            weaknesses = ["positioning", "consistency"]
            recommendations = ["Practice positioning", "Improve consistency"]
        else:
            analysis = (
                f"Developing player with K/D {kd_ratio:.2f} "
                f"and win rate {win_rate:.1f}%"
            )
            strengths = ["potential"]
            weaknesses = ["aim", "positioning", "game_sense"]
            recommendations = [
                "Practice aim training", 
                "Study positioning", 
                "Watch pro matches"
            ]

        # Simple training plan
        training_plan = {
            "focus_areas": weaknesses[:3],
            "daily_exercises": [
                {
                    "name": "Aim Training",
                    "duration": "30 minutes",
                    "description": "Practice on aim_botz",
                    "maps": ["aim_botz"]
                },
                {
                    "name": "Deathmatch",
                    "duration": "45 minutes", 
                    "description": "Improve reflexes and positioning",
                    "maps": ["de_mirage", "de_dust2"]
                }
            ],
            "weekly_goals": ["Improve K/D ratio", "Increase win rate"],
            "estimated_time": "2-4 weeks"
        }

        return PlayerAnalysisResponse(
            player_id=player_id,
            nickname=request.player_nickname,
            analysis=analysis,
            recommendations=recommendations,
            training_plan=training_plan,
            strengths=strengths,
            weaknesses=weaknesses
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing player: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze player"
        )


@router.get("/training-plan/{player_id}")
async def get_training_plan(player_id: str):
    """
    Get simple training plan
    """
    try:
        from ...integrations.faceit_client import FaceitAPIClient

        faceit_client = FaceitAPIClient()

        # Fetch statistics
        stats = await faceit_client.get_player_stats(player_id)
        if not stats:
            raise HTTPException(
                status_code=404, detail="Player stats not found"
            )

        # Simple training plan
        training_plan = {
            "focus_areas": ["aim", "positioning"],
            "daily_exercises": [
                {
                    "name": "Aim Training",
                    "duration": "30 minutes",
                    "description": "Practice on aim maps",
                    "maps": ["aim_botz"]
                }
            ],
            "weekly_goals": ["Improve aim", "Better positioning"],
            "estimated_time": "2-3 weeks"
        }

        return training_plan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating training plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate training plan"
        )
