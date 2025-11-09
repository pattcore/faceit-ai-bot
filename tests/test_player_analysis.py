"""
Tests for Player Analysis
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.server.features.player_analysis.service import PlayerAnalysisService
from src.server.features.player_analysis.schemas import PlayerStats


@pytest.fixture
def mock_faceit_client():
    """Mock Faceit API client"""
    client = Mock()
    client.get_player_by_nickname = AsyncMock(return_value={
        "player_id": "test123",
        "nickname": "TestPlayer",
        "games": {
            "cs2": {
                "faceit_elo": 2000,
                "skill_level": 8
            }
        }
    })
    client.get_player_stats = AsyncMock(return_value={
        "lifetime": {
            "Average K/D Ratio": "1.25",
            "Win Rate %": "55",
            "Headshots %": "48",
            "Average Kills": "18",
            "Matches": "200"
        }
    })
    client.get_match_history = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_ai_service():
    """Mock AI service"""
    service = Mock()
    service.analyze_player_with_ai = AsyncMock(return_value={
        "strengths": {
            "aim": 8,
            "game_sense": 7,
            "positioning": 6,
            "teamwork": 7,
            "consistency": 8
        },
        "weaknesses": {
            "areas": ["positioning"],
            "priority": "positioning",
            "recommendations": ["Practice positioning"]
        },
        "training_plan": {
            "focus_areas": ["positioning"],
            "daily_exercises": [{
                "name": "Position practice",
                "duration": "30 min",
                "description": "Practice holding positions"
            }],
            "estimated_time": "2-4 weeks"
        },
        "overall_rating": 7
    })
    return service


@pytest.mark.asyncio
async def test_analyze_player_success(mock_faceit_client, mock_ai_service):
    """Test successful player analysis"""
    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client
    service.ai_service = mock_ai_service
    
    result = await service.analyze_player("TestPlayer")
    
    assert result is not None
    assert result.nickname == "TestPlayer"
    assert result.player_id == "test123"
    assert result.overall_rating == 7
    assert result.stats.kd_ratio == 1.25
    assert result.stats.win_rate == 55.0


@pytest.mark.asyncio
async def test_analyze_player_not_found(mock_faceit_client, mock_ai_service):
    """Test player not found"""
    mock_faceit_client.get_player_by_nickname = AsyncMock(return_value=None)
    
    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client
    service.ai_service = mock_ai_service
    
    result = await service.analyze_player("NonExistent")
    
    assert result is None


@pytest.mark.asyncio
async def test_parse_stats():
    """Test stats parsing"""
    service = PlayerAnalysisService()
    
    stats_data = {
        "lifetime": {
            "Average K/D Ratio": "1.5",
            "Win Rate %": "60",
            "Headshots %": "50",
            "Average Kills": "20",
            "Matches": "300"
        }
    }
    
    player = {
        "games": {
            "cs2": {
                "faceit_elo": 2500,
                "skill_level": 10
            }
        }
    }
    
    stats = service._parse_stats(stats_data, player)
    
    assert stats.kd_ratio == 1.5
    assert stats.win_rate == 60.0
    assert stats.headshot_percentage == 50.0
    assert stats.average_kills == 20.0
    assert stats.matches_played == 300
    assert stats.elo == 2500
    assert stats.level == 10


def test_calculate_overall_rating():
    """Test overall rating calculation"""
    from src.server.features.player_analysis.schemas import PlayerStrengths
    
    service = PlayerAnalysisService()
    
    strengths = PlayerStrengths(
        aim=8,
        game_sense=7,
        positioning=6,
        teamwork=7,
        consistency=8
    )
    
    rating = service._calculate_overall_rating(strengths)
    
    assert 1 <= rating <= 10
    assert rating == 7  # (8+7+6+7+8)/5 = 7.2 -> 7
