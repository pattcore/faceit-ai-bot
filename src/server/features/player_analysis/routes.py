"""
Player Analysis Routes
Routes for player analysis
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from .service import PlayerAnalysisService
from .schemas import PlayerAnalysisRequest, PlayerAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("/{nickname}/analysis", response_model=PlayerAnalysisResponse)
async def analyze_player(
    nickname: str,
    service: PlayerAnalysisService = Depends()
):
    """
    Анализ игрока по никнейму
    
    Args:
        nickname: Player nickname на Faceit
        
    Returns:
        Детальный анализ игрока с рекомендациями
    """
    try:
        analysis = await service.analyze_player(nickname)
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
    service: PlayerAnalysisService = Depends()
):
    """
    Получить статистику игрока
    
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
    service: PlayerAnalysisService = Depends()
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
    service: PlayerAnalysisService = Depends()
):
    """
    Поиск игроков по никнейму
    
    Args:
        query: Поисковый запрос
        limit: Лимит результатов
        
    Returns:
        Список найденных игроков
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
