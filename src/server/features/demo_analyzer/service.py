from typing import List, Dict
from fastapi import UploadFile
from .models import DemoMetadata, PlayerPerformance, RoundAnalysis, DemoAnalysis
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))
from exceptions import DemoAnalysisException

logger = logging.getLogger(__name__)

class DemoAnalyzer:
    def __init__(self):
        # Инициализация AI сервисов
        from ...ai.openai_service import OpenAIService
        from ...integrations.faceit_client import FaceitAPIClient
        
        self.ai_service = OpenAIService()
        self.faceit_client = FaceitAPIClient()
        
        logger.info("DemoAnalyzer initialized with AI services")

    async def analyze_demo(self, demo_file: UploadFile) -> DemoAnalysis:
        try:
            # Валидация файла
            if not demo_file.filename or not demo_file.filename.endswith('.dem'):
                raise DemoAnalysisException(
                    detail="Invalid file format. Only .dem files are supported",
                    error_code="INVALID_FILE_FORMAT"
                )
            
            # Чтение и парсинг демо файла
            demo_data = await self._parse_demo_file(demo_file)
            
            # Анализ производительности игроков
            player_performances = await self._analyze_player_performance(demo_data)
            
            # Анализ раундов
            round_analysis = await self._analyze_rounds(demo_data)
            
            # Определение ключевых моментов
            key_moments = await self._identify_key_moments(demo_data)
            
            # Генерация рекомендаций
            recommendations = await self._generate_recommendations(
                player_performances,
                round_analysis,
                key_moments
            )
            
            return DemoAnalysis(
                demo_id=demo_data['match_id'],
                metadata={
                    'match_id': demo_data['match_id'],
                    'map_name': demo_data['map'],
                    'game_mode': demo_data['mode'],
                    'date_played': datetime.now(),
                    'duration': demo_data['duration'],
                    'score': demo_data['score']
                },
                overall_performance=player_performances,
                round_analysis=round_analysis,
                key_moments=key_moments,
                recommendations=recommendations,
                improvement_areas=await self._identify_improvement_areas(player_performances)
            )
            
        except DemoAnalysisException:
            raise
        except Exception as e:
            logger.exception("Failed to analyze demo")
            raise DemoAnalysisException(
                detail=f"Internal server error during demo analysis: {str(e)}",
                error_code="INTERNAL_ERROR",
                status_code=500
            )

    async def _parse_demo_file(self, demo_file: UploadFile) -> Dict:
        """Парсинг демо файла CS2"""
        # Demo parsing not implemented
        return {
            'match_id': '12345',
            'map': 'de_dust2',
            'mode': 'competitive',
            'duration': 2700,
            'score': {'team1': 16, 'team2': 14}
        }

    async def _analyze_player_performance(self, demo_data: Dict) -> Dict[str, PlayerPerformance]:
        """Analyze player performance"""
        # ML analysis not implemented
        return {}

    async def _analyze_rounds(self, demo_data: Dict) -> List[RoundAnalysis]:
        """Analyze rounds"""
        # Round analysis not implemented
        return []

    async def _identify_key_moments(self, demo_data: Dict) -> List[Dict]:
        """Определение ключевых моментов матча"""
        # Key moments detection not implemented
        return []

    async def _generate_recommendations(
        self,
        player_performances: Dict[str, PlayerPerformance],
        round_analysis: List[RoundAnalysis],
        key_moments: List[Dict]
    ) -> List[str]:
        """Генерация рекомендаций по улучшению игры с помощью AI"""
        try:
            # Подготовка данных для AI анализа
            stats_summary = {
                "total_players": len(player_performances),
                "rounds_analyzed": len(round_analysis),
                "key_moments_count": len(key_moments)
            }
            
            # Получение AI рекомендаций
            ai_analysis = await self.ai_service.analyze_player_performance(
                stats=stats_summary,
                match_history=[]
            )
            
            # Парсинг рекомендаций из AI ответа
            recommendations = self._parse_recommendations(ai_analysis)
            
            return recommendations if recommendations else self._get_default_recommendations()
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}")
            return self._get_default_recommendations()
    
    def _parse_recommendations(self, ai_text: str) -> List[str]:
        """Парсинг рекомендаций из AI текста"""
        lines = ai_text.split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                # Убираем маркеры списка
                clean_line = line.lstrip('-•0123456789. ')
                if clean_line:
                    recommendations.append(clean_line)
        
        return recommendations[:10]  # Максимум 10 рекомендаций
    
    def _get_default_recommendations(self) -> List[str]:
        """Дефолтные рекомендации"""
        return [
            "Улучшить прицеливание в голову",
            "Работать над экономикой команды",
            "Улучшить использование утилит",
            "Практиковать позиционирование",
            "Изучить тайминги на картах"
        ]

    async def _identify_improvement_areas(
        self,
        player_performances: Dict[str, PlayerPerformance]
    ) -> List[Dict]:
        """Определение областей для улучшения"""
        # Improvement areas analysis not implemented
        return [
            {
                "area": "aim",
                "current_level": "medium",
                "recommendation": "Тренировать точность прицеливания"
            }
        ]