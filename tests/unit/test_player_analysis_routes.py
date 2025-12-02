"""Unit tests for player analysis routes"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.server.features.player_analysis.routes import (
    router,
    PlayerAnalysisService,
    enforce_player_analysis_rate_limit,
)
from src.server.features.player_analysis.schemas import (
    PlayerAnalysisResponse,
    PlayerStats,
    PlayerStrengths,
    PlayerWeaknesses,
    TrainingPlan,
)
from src.server.middleware.rate_limiter import rate_limiter


@pytest.fixture
def app():
    """Создаем отдельное FastAPI-приложение только с роутами player_analysis."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_service():
    """Мок сервиса анализа игрока."""
    service = Mock(spec=PlayerAnalysisService)
    service.analyze_player = AsyncMock()
    service.get_player_stats = AsyncMock()
    service.get_player_matches = AsyncMock()
    service.search_players = AsyncMock()
    return service


@pytest.fixture
def client(app, mock_service):
    """TestClient с переопределенными зависимостями и выключенным rate limiting."""
    app.dependency_overrides[PlayerAnalysisService] = lambda: mock_service
    app.dependency_overrides[rate_limiter] = lambda: None
    app.dependency_overrides[enforce_player_analysis_rate_limit] = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analyze_player_route_success(client, mock_service):
    """Успешный анализ игрока через HTTP маршрут."""
    stats = PlayerStats(
        kd_ratio=1.2,
        win_rate=55.0,
        headshot_percentage=45.0,
        average_kills=18.0,
        matches_played=150,
        elo=2000,
        level=8,
    )
    strengths = PlayerStrengths(
        aim=8,
        game_sense=7,
        positioning=7,
        teamwork=6,
        consistency=7,
    )
    weaknesses = PlayerWeaknesses(
        areas=["positioning"],
        priority="positioning",
        recommendations=["Practice positioning"],
    )
    plan = TrainingPlan(
        focus_areas=["positioning"],
        daily_exercises=[
            {
                "name": "Position practice",
                "duration": "30 min",
                "description": "Practice holding positions",
            }
        ],
        estimated_time="2-4 weeks",
    )

    mock_service.analyze_player = AsyncMock(
        return_value=PlayerAnalysisResponse(
            player_id="test123",
            nickname="TestPlayer",
            stats=stats,
            strengths=strengths,
            weaknesses=weaknesses,
            training_plan=plan,
            overall_rating=7,
        )
    )

    response = client.get("/players/TestPlayer/analysis")

    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "TestPlayer"
    assert data["player_id"] == "test123"


@pytest.mark.asyncio
async def test_analyze_player_route_not_found(client, mock_service):
    """Если сервис возвращает None, маршрут отдает 404."""
    mock_service.analyze_player = AsyncMock(return_value=None)

    response = client.get("/players/Unknown/analysis")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_player_stats_route_success(client, mock_service):
    """Маршрут статистики игрока возвращает данные сервиса."""
    mock_service.get_player_stats = AsyncMock(
        return_value={
            "player_id": "test123",
            "nickname": "TestPlayer",
            "stats": {"some": "value"},
            "level": 8,
            "elo": 2000,
        }
    )

    response = client.get("/players/TestPlayer/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == "test123"
    assert data["level"] == 8


@pytest.mark.asyncio
async def test_get_player_stats_route_not_found(client, mock_service):
    """Если сервис вернул None, маршрут статистики отдает 404."""
    mock_service.get_player_stats = AsyncMock(return_value=None)

    response = client.get("/players/Unknown/stats")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_player_matches_route_success(client, mock_service):
    """Маршрут истории матчей возвращает список и total."""
    mock_service.get_player_matches = AsyncMock(
        return_value=[{"match_id": "m1"}, {"match_id": "m2"}],
    )

    response = client.get("/players/TestPlayer/matches?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["matches"]) == 2


@pytest.mark.asyncio
async def test_get_player_matches_route_error(client, mock_service):
    """При исключении в сервисе маршрут матчей отдает 500."""
    mock_service.get_player_matches = AsyncMock(side_effect=Exception("boom"))

    response = client.get("/players/TestPlayer/matches?limit=2")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch match history"


@pytest.mark.asyncio
async def test_search_players_route_success(client, mock_service):
    """Маршрут поиска игроков возвращает список и total."""
    mock_service.search_players = AsyncMock(
        return_value=[{"nickname": "Test1"}, {"nickname": "Test2"}],
    )

    response = client.get("/players/search?query=test&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["players"]) == 2


@pytest.mark.asyncio
async def test_search_players_route_error(client, mock_service):
    """При исключении в сервисе маршрут поиска отдает 500."""
    mock_service.search_players = AsyncMock(side_effect=Exception("boom"))

    response = client.get("/players/search?query=test&limit=10")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to search players"
