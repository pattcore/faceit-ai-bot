"""
Faceit API Client
Client for Faceit API integration
"""
import aiohttp
from typing import Optional, Dict, List
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)


class FaceitAPIClient:
    """Client for Faceit API"""
    
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
        Get player information by nickname
        
        Args:
            nickname: Player nickname on Faceit
            
        Returns:
            Player information or None
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
        Get player statistics
        
        Args:
            player_id: Player ID on Faceit
            game: Game (by default cs2)
            
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
            player_id: Player ID
            game: Game
            limit: Number of matches
            
        Returns:
            List of matches
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
        Search players by nickname
        
        Args:
            nickname: Nickname for search
            country: Country (optional)
            limit: Result limit
            
        Returns:
            List of found players
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
        """Mock data for testing"""
        return {
            "lifetime": {
                "K/D Ratio": "1.15",
                "Win Rate %": "52",
                "Headshots %": "45",
                "Average K/D Ratio": "1.15",
                "Matches": "150"
            }
        }
