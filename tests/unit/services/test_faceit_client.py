"""Unit tests for Faceit client"""

import pytest
from unittest.mock import Mock, patch


class TestFaceitClient:
    """Test Faceit API client"""

    def test_client_initialization(self):
        """Test client initialization"""
        from src.server.integrations.faceit_client import FaceitClient

        client = FaceitClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert hasattr(client, "get_player")
        assert hasattr(client, "get_player_stats")
        assert hasattr(client, "get_player_history")

    @patch("httpx.get")
    def test_get_player_success(self, mock_get):
        """Test successful player retrieval"""
        from src.server.integrations.faceit_client import FaceitClient

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "player_id": "test-player-123",
            "nickname": "test_player",
            "country": "RU",
            "games": {"cs2": {"skill_level": 7, "faceit_elo": 1500}},
        }
        mock_get.return_value = mock_response

        client = FaceitClient(api_key="test_key")
        result = client.get_player("test-player-123")

        assert result["player_id"] == "test-player-123"
        assert result["nickname"] == "test_player"
        assert result["games"]["cs2"]["skill_level"] == 7

    @patch("httpx.get")
    def test_get_player_not_found(self, mock_get):
        """Test player not found"""
        from src.server.integrations.faceit_client import FaceitClient

        # Mock 404 response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        client = FaceitClient(api_key="test_key")

        with pytest.raises(Exception, match="404 Not Found"):
            client.get_player("nonexistent-player")

    @patch("httpx.get")
    def test_get_player_stats(self, mock_get):
        """Test player stats retrieval"""
        from src.server.integrations.faceit_client import FaceitClient

        mock_response = Mock()
        mock_response.json.return_value = {
            "lifetime": {
                "matches": "150",
                "k_d_ratio": "1.25",
                "average_kdr": "1.25",
                "win_rate": "54.67",
                "wins": "82",
            }
        }
        mock_get.return_value = mock_response

        client = FaceitClient(api_key="test_key")
        result = client.get_player_stats("test-player-123")

        assert result["lifetime"]["matches"] == "150"
        assert result["lifetime"]["k_d_ratio"] == "1.25"
        assert result["lifetime"]["win_rate"] == "54.67"


class TestFaceitClientErrorHandling:
    """Test error handling in Faceit client"""

    @patch("httpx.get")
    def test_api_rate_limit(self, mock_get):
        """Test rate limit handling"""
        from src.server.integrations.faceit_client import FaceitClient

        # Mock rate limit response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")
        mock_get.return_value = mock_response

        client = FaceitClient(api_key="test_key")

        with pytest.raises(Exception, match="429 Too Many Requests"):
            client.get_player("test-player")

    @patch("httpx.get")
    def test_network_error(self, mock_get):
        """Test network error handling"""
        from src.server.integrations.faceit_client import FaceitClient

        mock_get.side_effect = Exception("Connection timeout")

        client = FaceitClient(api_key="test_key")

        with pytest.raises(Exception, match="Connection timeout"):
            client.get_player("test-player")
