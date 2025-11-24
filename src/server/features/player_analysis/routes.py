"""
Player Analysis Routes
Routes for player analysis
"""
import logging

from fastapi import APIRouter, HTTPException, Depends

from .service import PlayerAnalysisService
from .schemas import PlayerAnalysisResponse
from ...middleware.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{nickname}/analysis", response_model=PlayerAnalysisResponse)
async def analyze_player(
    nickname: str,
    language: str = "ru",
    service: PlayerAnalysisService = Depends(),
    _: None = Depends(rate_limiter),
):
    """
    Analyze player by nickname

    Args:
        nickname: Player nickname on Faceit

    Returns:
        Detailed player analysis with recommendations
    """
    try:
        analysis = await service.analyze_player(nickname, language=language)
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Player '{nickname}' not found"
            )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing player {nickname}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze player"
        )


@router.get("/{nickname}/stats")
async def get_player_stats(
    nickname: str,
    service: PlayerAnalysisService = Depends(),
    _: None = Depends(rate_limiter),
):
    """
    Get player statistics

    Args:
        nickname: Player nickname

    Returns:
        Player statistics
    """
    try:
        stats = await service.get_player_stats(nickname)
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Player '{nickname}' not found"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for {nickname}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch player stats"
        )


@router.get("/{nickname}/matches")
async def get_player_matches(
    nickname: str,
    limit: int = 20,
    service: PlayerAnalysisService = Depends(),
    _: None = Depends(rate_limiter),
):
    """
    Get player match history

    Args:
        nickname: Player nickname
        limit: Number of matches (by default 20)

    Returns:
        Match history
    """
    try:
        matches = await service.get_player_matches(nickname, limit)
        return {"matches": matches, "total": len(matches)}
    except Exception as e:
        logger.error(f"Error fetching matches for {nickname}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch match history"
        )


@router.get("/search")
async def search_players(
    query: str,
    limit: int = 20,
    service: PlayerAnalysisService = Depends(),
    _: None = Depends(rate_limiter),
):
    """
    Search players by nickname

    Args:
        query: Search query
        limit: Result limit

    Returns:
        List of found players
    """
    try:
        players = await service.search_players(query, limit)
        return {"players": players, "total": len(players)}
    except Exception as e:
        logger.error(f"Error searching players: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search players"
        )
