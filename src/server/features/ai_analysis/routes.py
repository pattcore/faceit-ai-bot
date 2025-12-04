"""AI Analysis API Routes"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...auth.dependencies import get_optional_current_user
from ...database.connection import get_db
from ...database.models import User
from ...integrations.faceit_client import FaceitAPIClient
from ...middleware.rate_limiter import rate_limiter
from ...services.ai_service import AIService
from ...services.rate_limit_service import rate_limit_service

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


async def enforce_ai_player_analysis_rate_limit(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    if current_user is None:
        return

    await rate_limit_service.enforce_user_operation_limit(
        db=db,
        user_id=current_user.id,
        operation="player_analysis",
    )


@router.post("/analyze-player", response_model=PlayerAnalysisResponse)
async def analyze_player(
    request: PlayerAnalysisRequest,
    language: str = "ru",
    _: None = Depends(rate_limiter),
    __: None = Depends(enforce_ai_player_analysis_rate_limit),
):
    """
    AI player analysis based on Faceit statistics

    Uses Groq AI for deep performance analysis
    and generating personalized recommendations
    """
    try:
        ai_service = AIService()
        faceit_client = FaceitAPIClient()

        # Fetch player data
        player_data = None
        if request.faceit_id:
            stats = await faceit_client.get_player_stats(request.faceit_id)
        else:
            player_data = await faceit_client.get_player_by_nickname(
                request.player_nickname
            )
            if player_data:
                stats = await faceit_client.get_player_stats(
                    player_data['player_id']
                )
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
            )
        }

        # Fetch match history
        player_id = request.faceit_id or player_data['player_id']
        match_history = await faceit_client.get_match_history(
            player_id, limit=20
        )

        # Analysis
        analysis = await ai_service.analyze_player_with_ai(
            nickname=request.player_nickname,
            stats=player_stats,
            match_history=match_history,
            language=language,
        )

        # Generate training plan (now async, Groq-based)
        training_plan = await ai_service.generate_training_plan(
            nickname=request.player_nickname,
            stats=player_stats,
            language=language,
        )

        # Parse analysis to extract strengths/weaknesses
        analysis_text = analysis.get(
            "detailed_analysis", "Analysis not available"
        )
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


@router.post("/training-plan/{player_id}")
async def get_training_plan(
    player_id: str,
    _: None = Depends(rate_limiter),
    __: None = Depends(enforce_ai_player_analysis_rate_limit),
):
    """
    Get personalized training plan
    """
    try:
        ai_service = AIService()
        faceit_client = FaceitAPIClient()

        # Fetch statistics
        stats = await faceit_client.get_player_stats(player_id)
        if not stats:
            raise HTTPException(
                status_code=404, detail="Player stats not found"
            )

        lifetime_stats = stats.get('lifetime', {})
        player_stats = {
            'kd_ratio': float(lifetime_stats.get('K/D Ratio', '1.0')),
            'win_rate': float(lifetime_stats.get('Win Rate %', '50')),
            'hs_percentage': float(lifetime_stats.get('Headshots %', '40'))
        }

        # Generate plan
        training_plan = await ai_service.generate_training_plan(
            nickname=player_id,
            stats=player_stats
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


def _parse_analysis(
    analysis_text: str
) -> tuple[List[str], List[str], List[str]]:
    """
    Parse analysis to extract structured data

    Returns:
        (strengths, weaknesses, recommendations)
    """
    strengths = []
    weaknesses = []
    recommendations = []

    lines = analysis_text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Determine section
        if 'strength' in line.lower():
            current_section = 'strengths'
            continue
        elif 'weakness' in line.lower():
            current_section = 'weaknesses'
            continue
        elif 'recommend' in line.lower():
            current_section = 'recommendations'
            continue

        # Extract items
        if line.startswith(('-', '•', '*')) or (line and line[0].isdigit()):
            clean_line = line.lstrip('-•*0123456789. ')
            if clean_line:
                if current_section == 'strengths':
                    strengths.append(clean_line)
                elif current_section == 'weaknesses':
                    weaknesses.append(clean_line)
                elif current_section == 'recommendations':
                    recommendations.append(clean_line)

    return strengths[:5], weaknesses[:5], recommendations[:10]
