"""
Player Analysis Service
Сервис для анализа игроков
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
    """Сервис анализа игроков"""
    
    def __init__(self):
        self.faceit_client = FaceitAPIClient()
        self.ai_service = AIService()
    
    async def analyze_player(self, nickname: str) -> Optional[PlayerAnalysisResponse]:
        """
        Полный анализ игрока
        
        Args:
            nickname: Никнейм игрока
            
        Returns:
            Детальный анализ или None
        """
        try:
            # Проверяем кэш
            cache_key = cache_service.get_player_cache_key(nickname)
            cached = await cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache hit for player {nickname}")
                return PlayerAnalysisResponse(**cached)
            
            logger.info(f"Cache miss for player {nickname}, analyzing...")
            # Получаем данные игрока
            player = await self.faceit_client.get_player_by_nickname(nickname)
            if not player:
                return None
            
            player_id = player.get("player_id")
            
            # Получаем статистику
            stats_data = await self.faceit_client.get_player_stats(player_id)
            if not stats_data:
                return None
            
            # Парсим статистику
            stats = self._parse_stats(stats_data, player)
            
            # Получаем историю матчей для AI анализа
            match_history = await self.faceit_client.get_match_history(player_id, limit=10)
            
            # Используем AI для анализа
            ai_analysis = await self.ai_service.analyze_player_with_ai(
                nickname,
                stats.dict(),
                match_history
            )
            
            # Парсим AI анализ
            strengths = PlayerStrengths(**ai_analysis["strengths"])
            weaknesses = PlayerWeaknesses(**ai_analysis["weaknesses"])
            training_plan = TrainingPlan(**ai_analysis["training_plan"])
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
            
            # Сохраняем в кэш (1 час)
            await cache_service.set(cache_key, result.dict(), ttl=3600)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing player {nickname}: {str(e)}")
            return None
    
    async def get_player_stats(self, nickname: str) -> Optional[Dict]:
        """Получить статистику игрока"""
        try:
            player = await self.faceit_client.get_player_by_nickname(nickname)
            if not player:
                return None
            
            player_id = player.get("player_id")
            stats = await self.faceit_client.get_player_stats(player_id)
            
            return {
                "player_id": player_id,
                "nickname": nickname,
                "stats": stats,
                "level": player.get("games", {}).get("cs2", {}).get("skill_level"),
                "elo": player.get("games", {}).get("cs2", {}).get("faceit_elo")
            }
        except Exception as e:
            logger.error(f"Error fetching stats for {nickname}: {str(e)}")
            return None
    
    async def get_player_matches(self, nickname: str, limit: int = 20) -> List[Dict]:
        """Получить историю матчей"""
        try:
            player = await self.faceit_client.get_player_by_nickname(nickname)
            if not player:
                return []
            
            player_id = player.get("player_id")
            matches = await self.faceit_client.get_match_history(player_id, limit=limit)
            
            return matches
        except Exception as e:
            logger.error(f"Error fetching matches for {nickname}: {str(e)}")
            return []
    
    async def search_players(self, query: str, limit: int = 20) -> List[Dict]:
        """Поиск игроков"""
        try:
            players = await self.faceit_client.search_players(query, limit=limit)
            return players
        except Exception as e:
            logger.error(f"Error searching players: {str(e)}")
            return []
    
    def _parse_stats(self, stats_data: Dict, player: Dict) -> PlayerStats:
        """Парсинг статистики из Faceit API"""
        lifetime = stats_data.get("lifetime", {})
        
        # Безопасное получение значений
        kd_ratio = float(lifetime.get("Average K/D Ratio", lifetime.get("K/D Ratio", "1.0")))
        win_rate = float(lifetime.get("Win Rate %", "50"))
        headshot_pct = float(lifetime.get("Headshots %", lifetime.get("Average Headshots %", "40")))
        avg_kills = float(lifetime.get("Average Kills", lifetime.get("Kills", "15")))
        matches = int(lifetime.get("Matches", "0"))
        
        # Данные из профиля игрока
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
    
    def _analyze_strengths(self, stats: PlayerStats) -> PlayerStrengths:
        """Анализ сильных сторон на основе статистики"""
        # Оценка прицеливания на основе K/D и headshot%
        aim_score = min(10, int((stats.kd_ratio * 4) + (stats.headshot_percentage / 10)))
        
        # Игровое чутье на основе win rate
        game_sense_score = min(10, int(stats.win_rate / 10))
        
        # Позиционирование (базовая оценка)
        positioning_score = min(10, max(5, int(stats.win_rate / 12)))
        
        # Командная игра (оценка на основе win rate и количества матчей)
        teamwork_score = min(10, int((stats.win_rate / 10) + (min(stats.matches_played, 100) / 20)))
        
        # Стабильность (на основе количества матчей)
        consistency_score = min(10, int(min(stats.matches_played, 500) / 50))
        
        return PlayerStrengths(
            aim=max(1, aim_score),
            game_sense=max(1, game_sense_score),
            positioning=max(1, positioning_score),
            teamwork=max(1, teamwork_score),
            consistency=max(1, consistency_score)
        )
    
    def _analyze_weaknesses(self, stats: PlayerStats) -> PlayerWeaknesses:
        """Анализ слабых сторон"""
        weaknesses = []
        recommendations = []
        
        if stats.kd_ratio < 1.0:
            weaknesses.append("aim")
            recommendations.append("Практиковать прицеливание на aim_botz и aim_training картах")
        
        if stats.headshot_percentage < 40:
            weaknesses.append("headshot accuracy")
            recommendations.append("Фокусироваться на headshot-only режимах")
        
        if stats.win_rate < 50:
            weaknesses.append("game sense")
            recommendations.append("Изучать профессиональные матчи и стратегии")
        
        if stats.matches_played < 50:
            weaknesses.append("experience")
            recommendations.append("Играть больше матчей для набора опыта")
        
        # Определяем приоритетную область
        priority = weaknesses[0] if weaknesses else "consistency"
        
        if not weaknesses:
            weaknesses = ["consistency"]
            recommendations = ["Продолжать поддерживать текущий уровень игры"]
        
        return PlayerWeaknesses(
            areas=weaknesses,
            priority=priority,
            recommendations=recommendations
        )
    
    def _generate_training_plan(self, weaknesses: PlayerWeaknesses) -> TrainingPlan:
        """Генерация плана тренировок"""
        focus_areas = weaknesses.areas[:3]  # Топ-3 области
        
        exercises = []
        
        if "aim" in focus_areas:
            exercises.append({
                "name": "Aim Training",
                "duration": "30 минут",
                "description": "Тренировка прицеливания на aim_botz"
            })
        
        if "headshot accuracy" in focus_areas:
            exercises.append({
                "name": "Headshot Practice",
                "duration": "20 минут",
                "description": "Headshot-only режим"
            })
        
        if "game sense" in focus_areas:
            exercises.append({
                "name": "Demo Review",
                "duration": "30 минут",
                "description": "Просмотр и анализ профессиональных матчей"
            })
        
        if "experience" in focus_areas:
            exercises.append({
                "name": "Competitive Matches",
                "duration": "2-3 матча",
                "description": "Игра в соревновательном режиме"
            })
        
        # Если нет специфичных упражнений
        if not exercises:
            exercises.append({
                "name": "General Practice",
                "duration": "1 час",
                "description": "Общая практика и поддержание формы"
            })
        
        return TrainingPlan(
            focus_areas=focus_areas,
            daily_exercises=exercises,
            estimated_time="2-4 недели"
        )
    
    def _calculate_overall_rating(self, strengths: PlayerStrengths) -> int:
        """Расчет общей оценки"""
        total = (
            strengths.aim +
            strengths.game_sense +
            strengths.positioning +
            strengths.teamwork +
            strengths.consistency
        )
        return min(10, max(1, int(total / 5)))
