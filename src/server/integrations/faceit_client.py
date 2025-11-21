"""
Faceit API Client
Client for Faceit API integration
"""
import aiohttp
from typing import Optional, Dict, List
import logging
from ..config.settings import settings
from ..exceptions import (
    FaceitAPIError,
    PlayerNotFoundError,
    FaceitAPIKeyMissingError,
    RateLimitExceededError
)

logger = logging.getLogger(__name__)


class FaceitAPIClient:
    """Client for Faceit API"""

    BASE_URL = "https://open.faceit.com/data/v4"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'FACEIT_API_KEY', None)
        if not self.api_key:
            logger.warning("Faceit API key not configured")
            # Will raise error when methods are called

        auth_header = (
            f"Bearer {self.api_key}"
            if self.api_key
            else ""
        )
        self.headers = {
            "Authorization": auth_header,
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
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
            raise FaceitAPIKeyMissingError()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/players",
                    headers=self.headers,
                    params={"nickname": nickname, "game": "cs2"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"Player not found: {nickname}")
                        raise PlayerNotFoundError(nickname)
                    elif response.status == 429:
                        logger.warning("Rate limit exceeded")
                        raise RateLimitExceededError()
                    else:
                        error_text = await response.text()
                        logger.error(f"Faceit API error {response.status}: {error_text}")
                        raise FaceitAPIError(
                            f"Faceit API returned status {response.status}",
                            status_code=response.status
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching player: {str(e)}")
            raise FaceitAPIError("Network error connecting to Faceit API")
        except Exception as e:
            if isinstance(e, (FaceitAPIError, PlayerNotFoundError, RateLimitExceededError)):
                raise
            logger.exception(f"Unexpected error fetching player: {str(e)}")
            raise FaceitAPIError("Unexpected error occurred")

    async def get_player_stats(
        self, player_id: str, game: str = "cs2"
    ) -> Optional[Dict]:
        """
        Get player statistics

        Args:
            player_id: Player ID on Faceit
            game: Game (by default cs2)

        Returns:
            Player statistics
        """
        if not self.api_key:
            raise FaceitAPIKeyMissingError()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/players/{player_id}/stats/{game}",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"Stats not found for player: {player_id}")
                        raise FaceitAPIError("Player statistics not found", status_code=404)
                    elif response.status == 429:
                        raise RateLimitExceededError()
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get stats {response.status}: {error_text}")
                        raise FaceitAPIError(
                            f"Failed to get statistics: {response.status}",
                            status_code=response.status
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching stats: {str(e)}")
            raise FaceitAPIError("Network error connecting to Faceit API")
        except Exception as e:
            if isinstance(e, (FaceitAPIError, RateLimitExceededError)):
                raise
            logger.exception(f"Unexpected error fetching stats: {str(e)}")
            raise FaceitAPIError("Unexpected error occurred")

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
            raise FaceitAPIKeyMissingError()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/players/{player_id}/history",
                    headers=self.headers,
                    params={"game": game, "limit": limit},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    elif response.status == 429:
                        raise RateLimitExceededError()
                    else:
                        logger.warning(f"Failed to get match history: {response.status}")
                        return []
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching match history: {str(e)}")
            return []
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error fetching match history: {str(e)}")
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
            raise FaceitAPIKeyMissingError()

        try:
            params = {"nickname": nickname, "limit": limit}
            if country:
                params["country"] = country

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/search/players",
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    elif response.status == 429:
                        raise RateLimitExceededError()
                    else:
                        logger.warning(f"Failed to search players: {response.status}")
                        return []
        except aiohttp.ClientError as e:
            logger.error(f"Network error searching players: {str(e)}")
            return []
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error searching players: {str(e)}")
            return []

    async def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Retrieve match details including demo URLs.

        This wraps the Data API endpoint `/matches/{match_id}`.
        """
        if not self.api_key:
            raise FaceitAPIKeyMissingError()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/matches/{match_id}",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"Match not found: {match_id}")
                        raise FaceitAPIError(
                            "Match not found",
                            status_code=404,
                        )
                    elif response.status == 429:
                        raise RateLimitExceededError()
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to get match details {response.status}: {error_text}"
                        )
                        raise FaceitAPIError(
                            f"Failed to get match details: {response.status}",
                            status_code=response.status,
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching match details: {str(e)}")
            raise FaceitAPIError("Network error connecting to Faceit API")
        except Exception as e:
            if isinstance(e, (FaceitAPIError, RateLimitExceededError)):
                raise
            logger.exception(f"Unexpected error fetching match details: {str(e)}")
            raise FaceitAPIError("Unexpected error occurred")

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
