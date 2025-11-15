"""Unit tests for configuration settings"""

import pytest
from unittest.mock import patch


class TestSettingsValidation:
    """Test settings validation"""

    def test_database_url_validation_valid(self):
        """Test valid database URLs"""
        from src.server.config.settings import Settings

        valid_urls = [
            "postgresql://user:pass@localhost:5432/db",
            "postgresql+asyncpg://user:pass@localhost:5432/db",
            "sqlite:///test.db",
        ]

        for url in valid_urls:
            with patch.dict("os.environ", {"DATABASE_URL": url}):
                settings = Settings()
                assert settings.DATABASE_URL == url

    def test_database_url_validation_invalid(self):
        """Test invalid database URLs"""
        from src.server.config.settings import Settings

        invalid_urls = [
            "mysql://user:pass@localhost:3306/db",
            "mongodb://localhost:27017/db",
            "invalid://url",
        ]

        for url in invalid_urls:
            with patch.dict("os.environ", {"DATABASE_URL": url}):
                with pytest.raises(ValueError, match="Invalid database URL"):
                    Settings()

    def test_secret_key_validation_valid(self):
        """Test valid secret key"""
        from src.server.config.settings import Settings

        valid_key = "a" * 32  # 32 characters
        with patch.dict("os.environ", {"SECRET_KEY": valid_key}):
            settings = Settings()
            assert settings.SECRET_KEY == valid_key

    def test_secret_key_validation_too_short(self):
        """Test secret key too short"""
        from src.server.config.settings import Settings

        short_key = "short"
        with patch.dict("os.environ", {"SECRET_KEY": short_key}):
            with pytest.raises(ValueError, match="must be at least 32 characters"):
                Settings()


class TestSettingsDefaults:
    """Test default settings values"""

    def test_app_settings_defaults(self):
        """Test application settings defaults"""
        from src.server.config.settings import Settings

        settings = Settings()
        assert settings.APP_TITLE == "Faceit AI Bot Service"
        assert settings.APP_VERSION == "0.4.0"
        assert settings.NODE_ENV == "production"

    def test_database_settings_defaults(self):
        """Test database settings defaults"""
        from src.server.config.settings import Settings

        settings = Settings()
        assert "postgresql://" in settings.DATABASE_URL
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379

    def test_cors_settings_defaults(self):
        """Test CORS settings defaults"""
        from src.server.config.settings import Settings

        settings = Settings()
        assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
        assert "https://pattmsc.online" in settings.ALLOWED_ORIGINS


class TestSettingsCaching:
    """Test settings caching with lru_cache"""

    def test_settings_singleton(self):
        """Test that settings are cached (singleton pattern)"""
        from src.server.config.settings import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2  # Same instance due to lru_cache
