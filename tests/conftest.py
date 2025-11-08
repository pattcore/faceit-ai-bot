"""
Глобальные фикстуры для тестов
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, AsyncMock
import os

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

# Устанавливаем переменные окружения для тестов
os.environ["TEST_ENV"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-min-32-characters-long-for-testing"
os.environ["FACEIT_API_KEY"] = "test-faceit-api-key"
os.environ["YOOKASSA_SHOP_ID"] = "test_shop_id"
os.environ["YOOKASSA_SECRET_KEY"] = "test_secret_key"


@pytest.fixture(scope="session")
def app():
    """Создание приложения для тестов"""
    from src.server.main import app
    return app


@pytest.fixture(scope="session")
def client(app):
    """Тестовый клиент"""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Мок настроек"""
    from unittest.mock import Mock
    settings = Mock()
    settings.APP_TITLE = "Faceit AI Bot Service Test"
    settings.APP_VERSION = "0.2.0"
    settings.DATABASE_URL = "sqlite:///./test.db"
    settings.SECRET_KEY = "test-secret-key-min-32-characters-long"
    settings.FACEIT_API_KEY = "test-api-key"
    settings.YOOKASSA_SHOP_ID = "test_shop_id"
    settings.YOOKASSA_SECRET_KEY = "test_secret_key"
    settings.WEBSITE_URL = "http://localhost:3000"
    settings.API_URL = "http://localhost:8000"
    settings.ALLOWED_ORIGINS = ["http://localhost:3000"]
    settings.TEST_ENV = True
    return settings


@pytest.fixture
def mock_db_session():
    """Мок сессии базы данных"""
    from unittest.mock import Mock
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def mock_demo_file():
    """Мок демо-файла"""
    from unittest.mock import Mock
    from io import BytesIO
    
    file = Mock()
    file.filename = "test_demo.dem"
    file.content_type = "application/octet-stream"
    file.size = 1024
    file.read = AsyncMock(return_value=b"fake demo file content")
    file.file = BytesIO(b"fake demo file content")
    return file


@pytest.fixture
def mock_invalid_demo_file():
    """Мок невалидного демо-файла"""
    from unittest.mock import Mock
    
    file = Mock()
    file.filename = "test_demo.txt"
    file.content_type = "text/plain"
    file.size = 1024
    return file


@pytest.fixture
def payment_request():
    """Фикстура для платежного запроса"""
    return {
        "amount": 500.0,
        "currency": "RUB",
        "description": "Demo analysis payment",
        "provider": "YOOKASSA",
        "user_id": "test_user_id"
    }


@pytest.fixture
def invalid_payment_request():
    """Фикстура для невалидного платежного запроса"""
    return {
        "amount": -100.0,
        "currency": "INVALID",
        "description": "",
        "provider": "INVALID",
        "user_id": ""
    }


@pytest.fixture
def teammate_preferences():
    """Фикстура для предпочтений поиска тиммейтов"""
    return {
        "min_elo": 1500,
        "max_elo": 2500,
        "region": "EU",
        "language": "ru",
        "playstyle": "aggressive"
    }


@pytest.fixture
def mock_faceit_api():
    """Мок Faceit API"""
    from unittest.mock import AsyncMock, Mock
    
    mock = Mock()
    mock.get_player_stats = AsyncMock(return_value={
        "faceit_elo": 2000,
        "matches_played": 100,
        "win_rate": 0.55,
        "avg_kd": 1.2,
        "avg_hs": 0.65,
        "favorite_maps": ["de_dust2", "de_mirage"],
        "last_20_matches": []
    })
    mock.get_match_history = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_payment_service():
    """Мок сервиса платежей"""
    from unittest.mock import AsyncMock, Mock
    
    service = Mock()
    service.create_payment = AsyncMock(return_value={
        "payment_id": "test_payment_id",
        "status": "pending",
        "payment_url": "https://payment.test.url",
        "amount": 500.0,
        "currency": "RUB"
    })
    service.check_payment_status = AsyncMock(return_value="pending")
    service.process_webhook = AsyncMock()
    return service


@pytest.fixture
def mock_demo_analyzer():
    """Мок анализатора демо"""
    from unittest.mock import AsyncMock, Mock
    
    analyzer = Mock()
    analyzer.analyze_demo = AsyncMock(return_value={
        "demo_id": "test_demo_id",
        "metadata": {
            "match_id": "12345",
            "map_name": "de_dust2",
            "game_mode": "competitive",
            "duration": 2700,
            "score": {"team1": 16, "team2": 14}
        },
        "overall_performance": {},
        "round_analysis": [],
        "key_moments": [],
        "recommendations": ["Улучшить прицеливание"],
        "improvement_areas": []
    })
    return analyzer


@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Очистка тестовой базы данных после каждого теста"""
    yield
    # Здесь можно добавить логику очистки БД
    test_db_path = Path("./test.db")
    if test_db_path.exists():
        test_db_path.unlink()

