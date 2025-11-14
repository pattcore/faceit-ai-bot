import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import UploadFile

from .models import (
    DemoAnalysis,
    PlayerPerformance,
    RoundAnalysis
)
from exceptions import DemoAnalysisException

logger = logging.getLogger(__name__)


class DemoAnalyzer:
    def __init__(self):
        # AI services initialization
        from ...services.ai_service import AIService
        from ...integrations.faceit_client import FaceitAPIClient

        self.ai_service = AIService()
        self.faceit_client = FaceitAPIClient()

        logger.info("DemoAnalyzer initialized with AI services")

    async def analyze_demo(
        self,
        demo_file: UploadFile
    ) -> DemoAnalysis:
        try:
            # File validation
            if (not demo_file.filename or
                    not demo_file.filename.endswith('.dem')):
                raise DemoAnalysisException(
                    detail=(
                        "Invalid file format. "
                        "Only .dem files are supported"
                    ),
                    error_code="INVALID_FILE_FORMAT"
                )

            # Read and parse demo file
            demo_data = await self._parse_demo_file(demo_file)

            # Player performance analysis
            player_performances = (
                await self._analyze_player_performance(demo_data)
            )

            # Round analysis
            round_analysis = await self._analyze_rounds(demo_data)

            # Identify key moments
            key_moments = await self._identify_key_moments(demo_data)

            # Generate recommendations
            recommendations = (
                await self._generate_recommendations(
                    player_performances,
                    round_analysis,
                    key_moments
                )
            )

            improvement_areas = (
                await self._identify_improvement_areas(
                    player_performances
                )
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
                improvement_areas=improvement_areas
            )

        except DemoAnalysisException:
            raise
        except Exception:
            logger.exception("Failed to analyze demo")
            raise DemoAnalysisException(
                detail=(
                    "Internal server error during demo analysis"
                ),
                error_code="INTERNAL_ERROR",
                status_code=500
            )

    async def _parse_demo_file(
        self,
        demo_file: UploadFile
    ) -> Dict:
        """Parse CS2 demo file"""
        # Demo parsing not implemented
        return {
            'match_id': '12345',
            'map': 'de_dust2',
            'mode': 'competitive',
            'duration': 2700,
            'score': {'team1': 16, 'team2': 14}
        }

    async def _analyze_player_performance(
        self,
        demo_data: Dict
    ) -> Dict[str, PlayerPerformance]:
        """Analyze player performance"""
        # ML analysis not implemented
        return {}

    async def _analyze_rounds(
        self,
        demo_data: Dict
    ) -> List[RoundAnalysis]:
        """Analyze rounds"""
        # Round analysis not implemented
        return []

    async def _identify_key_moments(
        self,
        demo_data: Dict
    ) -> List[Dict]:
        """Identify key match moments"""
        # Key moments detection not implemented
        return []

    async def _generate_recommendations(
        self,
        player_performances: Dict[str, PlayerPerformance],
        round_analysis: List[RoundAnalysis],
        key_moments: List[Dict]
    ) -> List[str]:
        """Generate improvement recommendations"""
        try:
            # Prepare data for analysis
            stats_summary = {
                "total_players": len(player_performances),
                "rounds_analyzed": len(round_analysis),
                "key_moments_count": len(key_moments)
            }

            # Get recommendations
            ai_analysis = (
                await self.ai_service.analyze_player_performance(
                    stats=stats_summary,
                    match_history=[]
                )
            )

            # Parse recommendations from response
            recommendations = self._parse_recommendations(
                ai_analysis
            )

            if recommendations:
                return recommendations
            return self._get_default_recommendations()

        except Exception:
            logger.exception(
                "Error generating recommendations"
            )
            return self._get_default_recommendations()

    def _parse_recommendations(
        self,
        ai_text: str
    ) -> List[str]:
        """Parse recommendations from text"""
        lines = ai_text.split('\n')
        recommendations = []

        for line in lines:
            line = line.strip()
            if (line and (
                    line.startswith('-') or
                    line.startswith('•') or
                    line[0].isdigit()
            )):
                # Remove list markers
                clean_line = line.lstrip('-•0123456789. ')
                if clean_line:
                    recommendations.append(clean_line)

        return recommendations[:10]

    def _get_default_recommendations(self) -> List[str]:
        """Default recommendations"""
        return [
            "Improve headshot aim",
            "Work on team economy",
            "Improve utility usage",
            "Practice positioning",
            "Learn map timings"
        ]

    async def _identify_improvement_areas(
        self,
        player_performances: Dict[str, PlayerPerformance]
    ) -> List[Dict]:
        """Identify improvement areas"""
        # Improvement areas analysis not implemented
        return [
            {
                "area": "aim",
                "current_level": "medium",
                "recommendation": "Train aiming accuracy"
            }
        ]
