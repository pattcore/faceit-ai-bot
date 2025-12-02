"""
Tests for Player Analysis
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException
from src.server.features.player_analysis.service import PlayerAnalysisService
from src.server.features.player_analysis.schemas import (
    PlayerStats,
    PlayerWeaknesses,
    TrainingPlan,
)


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
async def test_analyze_player_http_exception_propagated(
    mock_faceit_client,
    mock_ai_service,
):
    """HTTPException из Faceit клиента должен пробрасываться наружу."""
    mock_faceit_client.get_player_by_nickname = AsyncMock(
        side_effect=HTTPException(status_code=503, detail="Faceit error"),
    )

    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client
    service.ai_service = mock_ai_service

    with pytest.raises(HTTPException):
        await service.analyze_player("TestPlayer")


@pytest.mark.asyncio
async def test_analyze_player_generic_exception_returns_none(
    mock_faceit_client,
    mock_ai_service,
):
    """Любая необработанная ошибка должна приводить к None, а не падению сервиса."""
    mock_faceit_client.get_player_by_nickname = AsyncMock(
        side_effect=RuntimeError("unexpected error"),
    )

    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client
    service.ai_service = mock_ai_service

    result = await service.analyze_player("TestPlayer")

    assert result is None


@pytest.mark.asyncio
async def test_get_player_stats_success(mock_faceit_client):
    """Успешное получение статистики игрока."""
    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client

    result = await service.get_player_stats("TestPlayer")

    assert result is not None
    assert result["player_id"] == "test123"
    assert result["nickname"] == "TestPlayer"
    assert result["level"] == 8
    assert result["elo"] == 2000


@pytest.mark.asyncio
async def test_get_player_stats_player_not_found(mock_faceit_client):
    """Если игрок не найден, возвращается None."""
    mock_faceit_client.get_player_by_nickname = AsyncMock(return_value=None)

    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client

    result = await service.get_player_stats("UnknownPlayer")

    assert result is None


@pytest.mark.asyncio
async def test_get_player_stats_exception_returns_none(mock_faceit_client):
    """При ошибке в клиенте Faceit метод должен вернуть None."""
    mock_faceit_client.get_player_by_nickname = AsyncMock(
        side_effect=Exception("boom"),
    )

    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client

    result = await service.get_player_stats("TestPlayer")

    assert result is None


@pytest.mark.asyncio
async def test_get_player_matches_success(mock_faceit_client):
    """Успешное получение истории матчей игрока."""
    mock_faceit_client.get_match_history = AsyncMock(
        return_value=[{"match_id": "m1"}, {"match_id": "m2"}],
    )

    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client

    matches = await service.get_player_matches("TestPlayer", limit=5)

    assert len(matches) == 2
    assert matches[0]["match_id"] == "m1"


@pytest.mark.asyncio
async def test_get_player_matches_player_not_found(mock_faceit_client):
    """Если игрок не найден, история матчей пустая."""
    mock_faceit_client.get_player_by_nickname = AsyncMock(return_value=None)

    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client

    matches = await service.get_player_matches("UnknownPlayer")

    assert matches == []


@pytest.mark.asyncio
async def test_get_player_matches_exception_returns_empty(mock_faceit_client):
    """При ошибке в клиенте Faceit возвращается пустой список матчей."""
    mock_faceit_client.get_player_by_nickname = AsyncMock(
        side_effect=Exception("boom"),
    )

    service = PlayerAnalysisService()
    service.faceit_client = mock_faceit_client

    matches = await service.get_player_matches("TestPlayer")

    assert matches == []


@pytest.mark.asyncio
async def test_search_players_success():
    """Успешный поиск игроков."""
    service = PlayerAnalysisService()
    service.faceit_client = Mock()
    service.faceit_client.search_players = AsyncMock(
        return_value=[{"nickname": "Test1"}, {"nickname": "Test2"}],
    )

    players = await service.search_players("Test", limit=10)

    assert len(players) == 2
    assert players[0]["nickname"] == "Test1"


@pytest.mark.asyncio
async def test_search_players_exception_returns_empty():
    """При ошибке поиска возвращается пустой список игроков."""
    service = PlayerAnalysisService()
    service.faceit_client = Mock()
    service.faceit_client.search_players = AsyncMock(
        side_effect=Exception("search failed"),
    )

    players = await service.search_players("Test", limit=10)

    assert players == []


def test_internal_analysis_helpers_end_to_end():
    """Проверяем, что внутренние методы анализа работают согласованно."""
    service = PlayerAnalysisService()

    stats = PlayerStats(
        kd_ratio=0.8,
        win_rate=40.0,
        headshot_percentage=30.0,
        average_kills=10.0,
        matches_played=20,
        elo=1500,
        level=5,
    )

    strengths = service._analyze_strengths(stats)
    assert 1 <= strengths.aim <= 10
    assert 1 <= strengths.game_sense <= 10
    assert 1 <= strengths.positioning <= 10
    assert 1 <= strengths.teamwork <= 10
    assert 1 <= strengths.consistency <= 10

    weaknesses = service._analyze_weaknesses(stats)
    assert weaknesses.areas  # есть хотя бы одна слабая сторона
    assert weaknesses.priority in weaknesses.areas

    plan = service._generate_training_plan(weaknesses)
    assert isinstance(plan, TrainingPlan)
    assert plan.focus_areas
    assert plan.daily_exercises


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
