"""
Faceit API Client
Клиент для работы с Faceit API
"""
import aiohttp
from typing import Optional, Dict, List
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)


class FaceitAPIClient:
    """Клиент для Faceit API"""
    
    BASE_URL = "https://open.faceit.com/data/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'FACEIT_API_KEY', None)
        if not self.api_key:
            logger.warning("Faceit API key not configured")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Accept": "application/json"
        }
    
    async def get_player_by_nickname(self, nickname: str) -> Optional[Dict]:
        """
        Получить информацию об игроке по никнейму
        
        Args:
            nickname: Player nickname на Faceit
            
        Returns:
            Информация об игроке или None
        """
        if not self.api_key:
            logger.error("Faceit API key not configured")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/players",
                    headers=self.headers,
                    params={"nickname": nickname, "game": "cs2"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Faceit API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching player: {str(e)}")
            return None
    
    async def get_player_stats(self, player_id: str, game: str = "cs2") -> Optional[Dict]:
        """
        Получить статистику игрока
        
        Args:
            player_id: ID игрока на Faceit
            game: Игра (by default cs2)
            
        Returns:
            Player statistics
        """
        if not self.api_key:
            return self._get_mock_stats()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/players/{player_id}/stats/{game}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get stats: {response.status}")
                        return self._get_mock_stats()
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
            return self._get_mock_stats()
    
    async def get_match_history(
        self, 
        player_id: str,
        game: str = "cs2",
        limit: int = 20
    ) -> List[Dict]:
        """
        Get player match history
        
        Args:
            player_id: ID игрока
            game: Игра
            limit: Number of matches
            
        Returns:
            Список matches
        """
        if not self.api_key:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/players/{player_id}/history",
                    headers=self.headers,
                    params={"game": game, "limit": limit}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    return []
        except Exception as e:
            logger.error(f"Error fetching match history: {str(e)}")
            return []
    
    async def search_players(
        self,
        nickname: str,
        country: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Поиск игроков по никнейму
        
        Args:
            nickname: Никнейм для поиска
            country: Страна (опционально)
            limit: Лимит результатов
            
        Returns:
            Список найденных игроков
        """
        if not self.api_key:
            return []
        
        try:
            params = {"nickname": nickname, "limit": limit}
            if country:
                params["country"] = country
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/search/players",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    return []
        except Exception as e:
            logger.error(f"Error searching players: {str(e)}")
            return []
    
    def _get_mock_stats(self) -> Dict:
        """Моковые данные для тестирования"""
        return {
            "lifetime": {
                "K/D Ratio": "1.15",
                "Win Rate %": "52",
                "Headshots %": "45",
                "Average K/D Ratio": "1.15",
                "Matches": "150"
            }
        }
