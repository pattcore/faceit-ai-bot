import pytest
from unittest.mock import patch, MagicMock
from server.services.external_api_service import ExternalApiService
from server.services.gpt_service import GptService
from server.core.config import settings

@pytest.fixture
def mock_faceit_api():
    with patch('server.services.external_api_service.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "player": {
                "player_id": "test_id",
                "nickname": "test_player",
                "games": {
                    "csgo": {
                        "skill_level": 7,
                        "faceit_elo": 1800
                    }
                }
            }
        }
        yield mock_get

@pytest.fixture
def mock_gpt_api():
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_create.return_value = {
            "choices": [{
                "message": {
                    "content": "Тестовый ответ от GPT"
                }
            }]
        }
        yield mock_create

def test_faceit_api_player_stats(mock_faceit_api):
    """Test получения статистики игрока через FACEIT API"""
    api_service = ExternalApiService()
    stats = api_service.get_player_stats("test_player")
    
    assert stats is not None
    assert stats["player"]["nickname"] == "test_player"
    assert stats["player"]["games"]["csgo"]["skill_level"] == 7
    
    # Check that API was called with correct parameters
    mock_faceit_api.assert_called_once()
    assert "Authorization" in mock_faceit_api.call_args.kwargs["headers"]

def test_faceit_api_error_handling(mock_faceit_api):
    """Test обработки ошибок FACEIT API"""
    mock_faceit_api.return_value.status_code = 404
    mock_faceit_api.return_value.json.return_value = {"error": "Player not found"}
    
    api_service = ExternalApiService()
    with pytest.raises(Exception) as exc_info:
        api_service.get_player_stats("nonexistent_player")
    
    assert "Player not found" in str(exc_info.value)

def test_gpt_service_analysis(mock_gpt_api):
    """Test анализа демо через GPT"""
    gpt_service = GptService()
    analysis = gpt_service.analyze_demo_summary({
        "kills": 25,
        "deaths": 15,
        "assists": 5,
        "headshot_percentage": 65
    })
    
    assert analysis is not None
    assert isinstance(analysis, str)
    assert len(analysis) > 0
    
    # Check that GPT API was called with correct parameters
    mock_gpt_api.assert_called_once()
    call_args = mock_gpt_api.call_args.kwargs
    assert "messages" in call_args

def test_gpt_service_error_handling(mock_gpt_api):
    """Test обработки ошибок GPT API"""
    mock_gpt_api.side_effect = Exception("API Error")
    
    gpt_service = GptService()
    with pytest.raises(Exception) as exc_info:
        gpt_service.analyze_demo_summary({})
    
    assert "API Error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_api_service_caching():
    """Test кэширования результатов API запросов"""
    api_service = ExternalApiService()
    
    # First request should hit the API
    with patch('server.services.external_api_service.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "test"}
        
        result1 = await api_service.get_cached_player_stats("test_player")
        assert mock_get.call_count == 1
        
        # Second request should get data from cache
        result2 = await api_service.get_cached_player_stats("test_player")
        assert mock_get.call_count == 1  # Call count should not increase
        
        assert result1 == result2

@pytest.mark.asyncio
async def test_concurrent_api_requests():
    """Test одновременных запросов к API"""
    api_service = ExternalApiService()
    
    async def make_request(player_id):
        return await api_service.get_cached_player_stats(player_id)
    
    # Make several concurrent requests
    import asyncio
    tasks = [
        make_request(f"player_{i}")
        for i in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
    assert all(r is not None for r in results)