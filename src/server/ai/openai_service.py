"""
OpenAI Integration Service
Сервис для работы с GPT-4 и другими моделями OpenAI
"""
from typing import Dict, List, Optional
import logging
from openai import AsyncOpenAI
from ..config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Сервис для работы с OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', None)
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def analyze_player_performance(
        self, 
        stats: Dict,
        match_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Анализ производительности игрока с помощью GPT-4
        
        Args:
            stats: Текущая статистика игрока
            match_history: История последних матчей
            
        Returns:
            Детальный анализ и рекомендации
        """
        if not self.client:
            return "AI analysis unavailable - API key not configured"
        
        try:
            prompt = self._build_analysis_prompt(stats, match_history or [])
            
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты профессиональный CS2 тренер с опытом более 10 лет. "
                                 "Анализируй статистику игроков и давай конкретные, "
                                 "действенные рекомендации по улучшению игры."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error analyzing performance: {str(e)}"
    
    async def generate_training_plan(
        self,
        player_stats: Dict,
        focus_areas: List[str]
    ) -> Dict:
        """
        Генерация персонального плана тренировок
        
        Args:
            player_stats: Статистика игрока
            focus_areas: Области для улучшения
            
        Returns:
            Структурированный план тренировок
        """
        if not self.client:
            return self._get_default_training_plan()
        
        try:
            prompt = f"""
            Создай детальный план тренировок для CS2 игрока:
            
            Статистика:
            - K/D: {player_stats.get('kd_ratio', 'N/A')}
            - Headshot %: {player_stats.get('hs_percentage', 'N/A')}
            - Win Rate: {player_stats.get('win_rate', 'N/A')}
            
            Фокус на: {', '.join(focus_areas)}
            
            Верни JSON с полями: daily_exercises, weekly_goals, estimated_time
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Ты CS2 тренер. Отвечай только в JSON формате."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generating training plan: {str(e)}")
            return self._get_default_training_plan()
    
    def _build_analysis_prompt(self, stats: Dict, match_history: List[Dict]) -> str:
        """Построение промпта для анализа"""
        return f"""
        Проанализируй статистику CS2 игрока:
        
        Текущие показатели:
        - K/D Ratio: {stats.get('kd_ratio', 'N/A')}
        - Headshot %: {stats.get('hs_percentage', 'N/A')}
        - Win Rate: {stats.get('win_rate', 'N/A')}
        - Avg Damage: {stats.get('avg_damage', 'N/A')}
        - Matches Played: {stats.get('matches_played', 'N/A')}
        
        История последних матчей: {len(match_history)} матчей
        
        Дай подробный анализ:
        1. Сильные стороны
        2. Слабые стороны
        3. Конкретные рекомендации по улучшению
        4. План действий на ближайшую неделю
        """
    
    def _get_default_training_plan(self) -> Dict:
        """Дефолтный план тренировок"""
        return {
            "daily_exercises": [
                {
                    "name": "Aim Training",
                    "duration": 30,
                    "description": "Тренировка прицеливания на aim_botz"
                },
                {
                    "name": "Spray Control",
                    "duration": 20,
                    "description": "Контроль отдачи AK-47 и M4A4"
                }
            ],
            "weekly_goals": [
                "Увеличить точность на 5%",
                "Улучшить K/D до 1.2"
            ],
            "estimated_time": "2-3 недели"
        }
