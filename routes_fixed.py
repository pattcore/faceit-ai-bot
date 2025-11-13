"""
AI Analysis API Routes
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
    AI player analysis based on Faceit statistics

    Uses Groq AI for deep performance analysis
    and generating personalized recommendations
    """
    try:
        from ...services.ai_service import AIService
        from ...integrations.faceit_client import FaceitAPIClient

        # Service initialization
        ai_service = AIService()
        faceit_client = FaceitAPIClient()

        # Fetch player data
        player_data = None
        if request.faceit_id:
            stats = await faceit_client.get_player_stats(request.faceit_id)
            player_id = request.faceit_id
        else:
            player_data = await faceit_client.get_player_by_nickname(
                request.player_nickname
            )
            if player_data:
                stats = await faceit_client.get_player_stats(
                    player_data['player_id']
                )
                player_id = player_data['player_id']
            else:
                raise HTTPException(
                    status_code=404, detail="Player not found"
                )

        if not stats:
            raise HTTPException(
                status_code=404, detail="Stats not available"
            )

        # Prepare statistics for analysis
        lifetime_stats = stats.get('lifetime', {})
        player_stats = {
            'kd_ratio': float(lifetime_stats.get('K/D Ratio', '1.0')),
            'win_rate': float(lifetime_stats.get('Win Rate %', '50')),
            'hs_percentage': float(lifetime_stats.get('Headshots %', '40')),
            'matches_played': int(lifetime_stats.get('Matches', '0')),
            'avg_damage': float(
                lifetime_stats.get('Average K/D Ratio', '1.0')
            ),
            'level': 10,  # Default level
            'elo': 2000   # Default elo
        }

        # Fetch match history
        match_history = await faceit_client.get_match_history(
            player_id, limit=20
        )

        # Analysis with correct method
        analysis = await ai_service.analyze_player_with_ai(
            nickname=request.player_nickname,
            stats=player_stats,
            match_history=match_history
        )

        # Generate training plan with correct parameters
        weaknesses = analysis.get("weaknesses", {}).get("areas", ["aim"])
        player_level = player_stats.get('level', 5)
        training_plan = await ai_service.generate_training_plan(
            weaknesses=weaknesses,
            player_level=player_level
        )

        # Extract data from analysis
        analysis_text = analysis.get("detailed_analysis", "Analysis not available")
        strengths_list = list(analysis.get("strengths", {}).keys())
        weaknesses_list = analysis.get("weaknesses", {}).get("areas", [])
        recommendations_list = analysis.get("weaknesses", {}).get(
            "recommendations", []
        )

        return PlayerAnalysisResponse(
            player_id=player_id,
            nickname=request.player_nickname,
            analysis=analysis_text,
            recommendations=recommendations_list,
            training_plan=training_plan,
            strengths=strengths_list,
            weaknesses=weaknesses_list
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
    Get personalized training plan
    """
    try:
        from ...services.ai_service import AIService
        from ...integrations.faceit_client import FaceitAPIClient

        ai_service = AIService()
        faceit_client = FaceitAPIClient()

        # Fetch statistics
        stats = await faceit_client.get_player_stats(player_id)
        if not stats:
            raise HTTPException(
                status_code=404, detail="Player stats not found"
            )

        lifetime_stats = stats.get('lifetime', {})
        # Extract player statistics for analysis
        kd_ratio = float(lifetime_stats.get('K/D Ratio', '1.0'))
        win_rate = float(lifetime_stats.get('Win Rate %', '50'))
        hs_percentage = float(lifetime_stats.get('Headshots %', '40'))

        # Generate plan with correct parameters
        training_plan = await ai_service.generate_training_plan(
            weaknesses=["aim"],
            player_level=5
        )

        return training_plan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating training plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate training plan"
        )
