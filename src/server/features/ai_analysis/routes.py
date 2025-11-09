"""
AI Analysis API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
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
    AI анализ игрока на основе статистики Faceit
    
    Использует GPT-4 для глубокого анализа производительности
    и генерации персональных рекомендаций
    """
    try:
        from ...ai.openai_service import OpenAIService
        from ...integrations.faceit_client import FaceitAPIClient
        
        # Service initialization
        ai_service = OpenAIService()
        faceit_client = FaceitAPIClient()
        
        # Получение данных игрока
        player_data = None
        if request.faceit_id:
            stats = await faceit_client.get_player_stats(request.faceit_id)
        else:
            player_data = await faceit_client.get_player_by_nickname(request.player_nickname)
            if player_data:
                stats = await faceit_client.get_player_stats(player_data['player_id'])
            else:
                raise HTTPException(status_code=404, detail="Player not found")
        
        if not stats:
            raise HTTPException(status_code=404, detail="Stats not available")
        
        # Подготовка статистики для AI
        lifetime_stats = stats.get('lifetime', {})
        player_stats = {
            'kd_ratio': float(lifetime_stats.get('K/D Ratio', '1.0')),
            'win_rate': float(lifetime_stats.get('Win Rate %', '50')),
            'hs_percentage': float(lifetime_stats.get('Headshots %', '40')),
            'matches_played': int(lifetime_stats.get('Matches', '0')),
            'avg_damage': float(lifetime_stats.get('Average K/D Ratio', '1.0'))
        }
        
        # Fetch match history
        player_id = request.faceit_id or player_data['player_id']
        match_history = await faceit_client.get_match_history(player_id, limit=20)
        
        # AI анализ
        analysis = await ai_service.analyze_player_performance(
            stats=player_stats,
            match_history=match_history
        )
        
        # Генерация плана тренировок
        training_plan = await ai_service.generate_training_plan(
            player_stats=player_stats,
            focus_areas=['aim', 'positioning', 'game_sense']
        )
        
        # Парсинг анализа для извлечения сильных/слабых сторон
        strengths, weaknesses, recommendations = _parse_analysis(analysis)
        
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
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/training-plan/{player_id}")
async def get_training_plan(player_id: str):
    """
    Получить персональный план тренировок
    """
    try:
        from ...ai.openai_service import OpenAIService
        from ...integrations.faceit_client import FaceitAPIClient
        
        ai_service = OpenAIService()
        faceit_client = FaceitAPIClient()
        
        # Получение статистики
        stats = await faceit_client.get_player_stats(player_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        
        lifetime_stats = stats.get('lifetime', {})
        player_stats = {
            'kd_ratio': float(lifetime_stats.get('K/D Ratio', '1.0')),
            'win_rate': float(lifetime_stats.get('Win Rate %', '50')),
            'hs_percentage': float(lifetime_stats.get('Headshots %', '40'))
        }
        
        # Генерация плана
        training_plan = await ai_service.generate_training_plan(
            player_stats=player_stats,
            focus_areas=['aim', 'spray_control', 'positioning']
        )
        
        return training_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating training plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _parse_analysis(analysis_text: str) -> tuple[List[str], List[str], List[str]]:
    """
    Парсинг AI анализа для извлечения структурированных данных
    
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
        
        # Определение секции
        if 'сильн' in line.lower() or 'strength' in line.lower():
            current_section = 'strengths'
            continue
        elif 'слаб' in line.lower() or 'weakness' in line.lower():
            current_section = 'weaknesses'
            continue
        elif 'рекоменд' in line.lower() or 'recommend' in line.lower():
            current_section = 'recommendations'
            continue
        
        # Извлечение пунктов
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
