"""
Unit тесты для сервиса поиска тиммейтов
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.server.features.teammates.service import TeammateService
from src.server.features.teammates.models import TeammatePreferences, PlayerStats


@pytest.mark.unit
class TestTeammateService:
    """Тесты для TeammateService"""
    
    @pytest.fixture
    def teammate_service(self):
        """Создание сервиса поиска тиммейтов"""
        return TeammateService()
    
    @pytest.fixture
    def preferences(self):
        """Фикстура предпочтений"""
        return TeammatePreferences(
            min_elo=1500,
            max_elo=2500,
            region="EU",
            language="ru"
        )
    
    @pytest.mark.asyncio
    async def test_find_teammates(self, teammate_service, preferences):
        """Тест поиска тиммейтов"""
        user_id = "test_user_id"
        
        result = await teammate_service.find_teammates(user_id, preferences)
        
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_player_stats(self, teammate_service):
        """Тест получения статистики игрока"""
        user_id = "test_user_id"
        
        stats = await teammate_service._get_player_stats(user_id)
        
        assert stats is not None
        assert isinstance(stats, PlayerStats)
        assert stats.faceit_elo == 2000
        assert stats.matches_played == 100
        assert stats.win_rate == 0.55
    
    @pytest.mark.asyncio
    async def test_find_matching_players(self, teammate_service, preferences):
        """Тест поиска подходящих игроков"""
        user_stats = PlayerStats(
            faceit_elo=2000,
            matches_played=100,
            win_rate=0.55,
            avg_kd=1.2,
            avg_hs=0.65,
            favorite_maps=['de_dust2', 'de_mirage'],
            last_20_matches=[]
        )
        
        result = await teammate_service._find_matching_players(user_stats, preferences)
        
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_rank_players(self, teammate_service, preferences):
        """Тест ранжирования игроков"""
        from src.server.features.teammates.models import TeammateProfile
        
        players = [
            TeammateProfile(
                user_id="player1",
                username="Player1",
                faceit_elo=2000,
                region="EU",
                language="ru"
            ),
            TeammateProfile(
                user_id="player2",
                username="Player2",
                faceit_elo=1800,
                region="EU",
                language="ru"
            )
        ]
        
        result = await teammate_service._rank_players(players, preferences)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == len(players)
    
    def test_calculate_compatibility_score(self, teammate_service, preferences):
        """Тест расчета оценки совместимости"""
        from src.server.features.teammates.models import TeammateProfile
        
        player = TeammateProfile(
            user_id="player1",
            username="Player1",
            faceit_elo=2000,
            region="EU",
            language="ru"
        )
        
        score = teammate_service._calculate_compatibility_score(player, preferences)
        
        assert score is not None
        assert isinstance(score, float)
    
    @pytest.mark.asyncio
    async def test_update_preferences(self, teammate_service, preferences):
        """Тест обновления предпочтений"""
        user_id = "test_user_id"
        
        result = await teammate_service.update_preferences(user_id, preferences)
        
        assert result is not None
        assert result.min_elo == preferences.min_elo
        assert result.max_elo == preferences.max_elo
        assert result.region == preferences.region

