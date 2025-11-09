"""
AI Service для анализа игроков
Uses Groq API (free, fast)
"""
import os
import logging
from typing import Dict, List, Optional
import aiohttp
import json

logger = logging.getLogger(__name__)


class AIService:
    """Service for intelligent analysis"""
    
    def __init__(self):
        # Groq API (free, fast)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-70b-versatile"  # Free model
        
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set, AI analysis will be limited")
    
    async def analyze_player_with_ai(
        self,
        nickname: str,
        stats: Dict,
        match_history: List[Dict]
    ) -> Dict[str, any]:
        """
        Analyze player with AI
        
        Args:
            nickname: Player nickname
            stats: Player statistics
            match_history: Match history
            
        Returns:
            Detailed analysis
        """
        if not self.groq_api_key:
            return self._get_rule_based_analysis(stats)
        
        try:
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(nickname, stats, match_history)
            
            # Request to Groq API
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
        """Create prompt for analysis"""
        
        # Extract key metrics
        kd = stats.get("kd_ratio", 1.0)
        win_rate = stats.get("win_rate", 50.0)
        hs_pct = stats.get("headshot_percentage", 40.0)
        matches = stats.get("matches_played", 0)
        elo = stats.get("elo", 1000)
        level = stats.get("level", 5)
        
        # Recent matches analysis
        recent_performance = "No data"
        if match_history:
            recent_matches = match_history[:5]
            recent_performance = f"Last {len(recent_matches)} matches"
        
        prompt = f"""You are a professional CS2 analyst. Analyze the player and provide specific recommendations.

Player: {nickname}
Faceit Level: {level}
ELO: {elo}

Statistics:
- K/D Ratio: {kd}
- Win Rate: {win_rate}%
- Headshot %: {hs_pct}%
- Matches played: {matches}

{recent_performance}

Provide analysis in JSON format:
{{
  "strengths": {{
    "aim": <rating 1-10>,
    "game_sense": <rating 1-10>,
    "positioning": <rating 1-10>,
    "teamwork": <rating 1-10>,
    "consistency": <rating 1-10>
  }},
  "weaknesses": {{
    "areas": ["area1", "area2"],
    "priority": "main_issue",
    "recommendations": ["tip1", "tip2", "tip3"]
  }},
  "training_plan": {{
    "focus_areas": ["area1", "area2"],
    "daily_exercises": [
      {{"name": "exercise", "duration": "time", "description": "description"}}
    ],
    "estimated_time": "2-4 weeks"
  }},
  "overall_rating": <1-10>,
  "detailed_analysis": "Detailed player analysis in Russian (2-3 sentences)"
}}

Reply ONLY with JSON, no additional text."""

        return prompt
    
    async def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API"""
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
        """Parse analysis response"""
        try:
            # Remove markdown if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            analysis = json.loads(response)
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Response was: {response}")
            raise
    
    def _get_rule_based_analysis(self, stats: Dict) -> Dict:
        """Basic rule-based analysis (fallback)"""
        kd = stats.get("kd_ratio", 1.0)
        win_rate = stats.get("win_rate", 50.0)
        hs_pct = stats.get("headshot_percentage", 40.0)
        matches = stats.get("matches_played", 0)
        
        # Simple evaluation rules
        aim_score = min(10, int((kd * 4) + (hs_pct / 10)))
        game_sense_score = min(10, int(win_rate / 10))
        positioning_score = min(10, max(5, int(win_rate / 12)))
        teamwork_score = min(10, int((win_rate / 10) + (min(matches, 100) / 20)))
        consistency_score = min(10, int(min(matches, 500) / 50))
        
        weaknesses = []
        recommendations = []
        
        if kd < 1.0:
            weaknesses.append("aim")
            recommendations.append("Practice aim on aim_botz and aim_training maps")
        
        if hs_pct < 40:
            weaknesses.append("headshot accuracy")
            recommendations.append("Play headshot-only modes")
        
        if win_rate < 50:
            weaknesses.append("game sense")
            recommendations.append("Study professional matches and tactics")
        
        if not weaknesses:
            weaknesses = ["consistency"]
            recommendations = ["Continue maintaining current skill level"]
        
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
                "priority": weaknesses[0] if weaknesses else "consistency",
                "recommendations": recommendations
            },
            "training_plan": {
                "focus_areas": weaknesses[:3],
                "daily_exercises": [
                    {
                        "name": "Aim Training",
                        "duration": "30 minutes",
                        "description": "Aim training"
                    }
                ],
                "estimated_time": "2-4 weeks"
            },
            "overall_rating": max(1, overall),
            "detailed_analysis": f"Player shows {'good' if overall >= 6 else 'average'} results. Main areas for improvement: {', '.join(weaknesses)}."
        }
    
    async def generate_training_plan(
        self,
        weaknesses: List[str],
        player_level: int
    ) -> Dict:
        """Generate personalized training plan"""
        if not self.groq_api_key:
            return self._get_basic_training_plan(weaknesses)
        
        try:
            prompt = f"""Create detailed training plan for CS2 player level {player_level}.

Weaknesses: {', '.join(weaknesses)}

Create plan in JSON format:
{{
  "focus_areas": ["area1", "area2"],
  "daily_exercises": [
    {{
      "name": "name",
      "duration": "time",
      "description": "detailed description",
      "maps": ["map1", "map2"]
    }}
  ],
  "weekly_goals": ["цель1", "цель2"],
  "estimated_time": "improvement time"
}}

Reply ONLY with JSON."""

            response = await self._call_groq_api(prompt)
            return self._parse_ai_response(response)
            
        except Exception as e:
            logger.error(f"Training plan generation error: {e}")
            return self._get_basic_training_plan(weaknesses)
    
    def _get_basic_training_plan(self, weaknesses: List[str]) -> Dict:
        """Basic training plan"""
        exercises = []
        
        if "aim" in weaknesses or "aim" in weaknesses:
            exercises.append({
                "name": "Aim Training",
                "duration": "30 minutes",
                "description": "Training on aim_botz",
                "maps": ["aim_botz", "aim_training"]
            })
        
        if "headshot accuracy" in weaknesses:
            exercises.append({
                "name": "Headshot Practice",
                "duration": "20 minutes",
                "description": "Headshot-only mode",
                "maps": ["aim_botz"]
            })
        
        return {
            "focus_areas": weaknesses[:3],
            "daily_exercises": exercises if exercises else [
                {
                    "name": "General Practice",
                    "duration": "1 hour",
                    "description": "General practice",
                    "maps": ["de_dust2", "de_mirage"]
                }
            ],
            "weekly_goals": ["Improve statistics", "Improve consistency"],
            "estimated_time": "2-4 weeks"
        }
