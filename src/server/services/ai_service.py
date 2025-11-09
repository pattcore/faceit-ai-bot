"""
AI Service для анализа игроков
Использует Groq API (бесплатный, быстрый)
"""
import os
import logging
from typing import Dict, List, Optional
import aiohttp
import json

logger = logging.getLogger(__name__)


class AIService:
    """Сервис для работы с AI моделью"""
    
    def __init__(self):
        # Groq API (бесплатный, быстрый)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-70b-versatile"  # Бесплатная модель
        
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set, AI analysis will be limited")
    
    async def analyze_player_with_ai(
        self,
        nickname: str,
        stats: Dict,
        match_history: List[Dict]
    ) -> Dict[str, any]:
        """
        Анализ игрока с помощью AI
        
        Args:
            nickname: Никнейм игрока
            stats: Статистика игрока
            match_history: История матчей
            
        Returns:
            Детальный AI-анализ
        """
        if not self.groq_api_key:
            return self._get_rule_based_analysis(stats)
        
        try:
            # Формируем промпт для AI
            prompt = self._create_analysis_prompt(nickname, stats, match_history)
            
            # Запрос к Groq API
            analysis = await self._call_groq_api(prompt)
            
            return self._parse_ai_response(analysis)
            
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return self._get_rule_based_analysis(stats)
    
    def _create_analysis_prompt(
        self,
        nickname: str,
        stats: Dict,
        match_history: List[Dict]
    ) -> str:
        """Создание промпта для AI"""
        
        # Извлекаем ключевые метрики
        kd = stats.get("kd_ratio", 1.0)
        win_rate = stats.get("win_rate", 50.0)
        hs_pct = stats.get("headshot_percentage", 40.0)
        matches = stats.get("matches_played", 0)
        elo = stats.get("elo", 1000)
        level = stats.get("level", 5)
        
        # Анализ последних матчей
        recent_performance = "Нет данных"
        if match_history:
            recent_matches = match_history[:5]
            recent_performance = f"Последние {len(recent_matches)} матчей"
        
        prompt = f"""Ты - профессиональный аналитик CS2. Проанализируй игрока и дай конкретные рекомендации.

Игрок: {nickname}
Уровень Faceit: {level}
ELO: {elo}

Статистика:
- K/D Ratio: {kd}
- Win Rate: {win_rate}%
- Headshot %: {hs_pct}%
- Сыграно матчей: {matches}

{recent_performance}

Дай анализ в формате JSON:
{{
  "strengths": {{
    "aim": <оценка 1-10>,
    "game_sense": <оценка 1-10>,
    "positioning": <оценка 1-10>,
    "teamwork": <оценка 1-10>,
    "consistency": <оценка 1-10>
  }},
  "weaknesses": {{
    "areas": ["область1", "область2"],
    "priority": "главная_проблема",
    "recommendations": ["совет1", "совет2", "совет3"]
  }},
  "training_plan": {{
    "focus_areas": ["область1", "область2"],
    "daily_exercises": [
      {{"name": "упражнение", "duration": "время", "description": "описание"}}
    ],
    "estimated_time": "2-4 недели"
  }},
  "overall_rating": <1-10>,
  "detailed_analysis": "Детальный анализ игрока на русском языке (2-3 предложения)"
}}

Отвечай ТОЛЬКО JSON, без дополнительного текста."""

        return prompt
    
    async def _call_groq_api(self, prompt: str) -> str:
        """Вызов Groq API"""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты профессиональный аналитик CS2. Отвечай только в формате JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.groq_base_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Groq API error: {response.status} - {error_text}")
                    raise Exception(f"Groq API error: {response.status}")
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Парсинг ответа AI"""
        try:
            # Убираем markdown если есть
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            # Парсим JSON
            analysis = json.loads(response)
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Response was: {response}")
            raise
    
    def _get_rule_based_analysis(self, stats: Dict) -> Dict:
        """Базовый анализ без AI (fallback)"""
        kd = stats.get("kd_ratio", 1.0)
        win_rate = stats.get("win_rate", 50.0)
        hs_pct = stats.get("headshot_percentage", 40.0)
        matches = stats.get("matches_played", 0)
        
        # Простые правила для оценки
        aim_score = min(10, int((kd * 4) + (hs_pct / 10)))
        game_sense_score = min(10, int(win_rate / 10))
        positioning_score = min(10, max(5, int(win_rate / 12)))
        teamwork_score = min(10, int((win_rate / 10) + (min(matches, 100) / 20)))
        consistency_score = min(10, int(min(matches, 500) / 50))
        
        weaknesses = []
        recommendations = []
        
        if kd < 1.0:
            weaknesses.append("прицеливание")
            recommendations.append("Практиковать aim на aim_botz и aim_training картах")
        
        if hs_pct < 40:
            weaknesses.append("точность хедшотов")
            recommendations.append("Играть в headshot-only режимах")
        
        if win_rate < 50:
            weaknesses.append("игровое чутье")
            recommendations.append("Изучать профессиональные матчи и тактики")
        
        if not weaknesses:
            weaknesses = ["стабильность"]
            recommendations = ["Продолжать поддерживать текущий уровень"]
        
        overall = int((aim_score + game_sense_score + positioning_score + teamwork_score + consistency_score) / 5)
        
        return {
            "strengths": {
                "aim": max(1, aim_score),
                "game_sense": max(1, game_sense_score),
                "positioning": max(1, positioning_score),
                "teamwork": max(1, teamwork_score),
                "consistency": max(1, consistency_score)
            },
            "weaknesses": {
                "areas": weaknesses,
                "priority": weaknesses[0] if weaknesses else "стабильность",
                "recommendations": recommendations
            },
            "training_plan": {
                "focus_areas": weaknesses[:3],
                "daily_exercises": [
                    {
                        "name": "Aim Training",
                        "duration": "30 минут",
                        "description": "Тренировка прицеливания"
                    }
                ],
                "estimated_time": "2-4 недели"
            },
            "overall_rating": max(1, overall),
            "detailed_analysis": f"Игрок показывает {'хорошие' if overall >= 6 else 'средние'} результаты. Основные области для улучшения: {', '.join(weaknesses)}."
        }
    
    async def generate_training_plan(
        self,
        weaknesses: List[str],
        player_level: int
    ) -> Dict:
        """Генерация персонального плана тренировок"""
        if not self.groq_api_key:
            return self._get_basic_training_plan(weaknesses)
        
        try:
            prompt = f"""Создай детальный план тренировок для CS2 игрока уровня {player_level}.

Слабые стороны: {', '.join(weaknesses)}

Создай план в формате JSON:
{{
  "focus_areas": ["область1", "область2"],
  "daily_exercises": [
    {{
      "name": "название",
      "duration": "время",
      "description": "детальное описание",
      "maps": ["карта1", "карта2"]
    }}
  ],
  "weekly_goals": ["цель1", "цель2"],
  "estimated_time": "время улучшения"
}}

Отвечай ТОЛЬКО JSON."""

            response = await self._call_groq_api(prompt)
            return self._parse_ai_response(response)
            
        except Exception as e:
            logger.error(f"Training plan generation error: {e}")
            return self._get_basic_training_plan(weaknesses)
    
    def _get_basic_training_plan(self, weaknesses: List[str]) -> Dict:
        """Базовый план тренировок"""
        exercises = []
        
        if "прицеливание" in weaknesses or "aim" in weaknesses:
            exercises.append({
                "name": "Aim Training",
                "duration": "30 минут",
                "description": "Тренировка на aim_botz",
                "maps": ["aim_botz", "aim_training"]
            })
        
        if "точность хедшотов" in weaknesses:
            exercises.append({
                "name": "Headshot Practice",
                "duration": "20 минут",
                "description": "Headshot-only режим",
                "maps": ["aim_botz"]
            })
        
        return {
            "focus_areas": weaknesses[:3],
            "daily_exercises": exercises if exercises else [
                {
                    "name": "General Practice",
                    "duration": "1 час",
                    "description": "Общая практика",
                    "maps": ["de_dust2", "de_mirage"]
                }
            ],
            "weekly_goals": ["Улучшить статистику", "Повысить стабильность"],
            "estimated_time": "2-4 недели"
        }
