"""
Pytest fixtures для integration тестов
Тестирование взаимодействия компонентов с реальными зависимостями
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from faker import Faker
from unittest.mock import patch
from datetime import datetime

from src.server.config.settings import Settings
from src.server.database import Base
from src.server.database.connection import get_db
from src.server.main import app as fastapi_app
from src.server.auth.dependencies import get_current_user


# ============================================
# TEST DATABASE SETUP
# ============================================


@pytest.fixture(scope="session")
def test_db_url():
    """URL тестовой базы данных"""
    # Используем в-memory SQLite для скорости
    # Или реальный PostgreSQL если нужно протестировать специфическое поведение
    return os.getenv("TEST_DATABASE_URL", "sqlite:///./test_integration.db")


@pytest.fixture(scope="session")
def test_db_engine(test_db_url):
    """Создание движка тестовой БД"""
    connect_args = {}
    if test_db_url.startswith("sqlite"):
        # Используем в-memory SQLite для скорости
        # Или реальный PostgreSQL если нужно протестировать специфическое поведение
        connect_args = {"check_same_thread": False}

    engine = create_engine(test_db_url, echo=False, connect_args=connect_args)
    # Обнуляем схему, если файл БД уже существует от прошлых прогонов
    Base.metadata.drop_all(bind=engine)
    # Создаем все таблицы для текущего тестового запуска
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine):
    """Сессия тестовой БД с rollback после каждого теста"""
    # Создаем соединение и сессию
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    # Переопределяем генератор DB сессий в приложении
    def override_get_db():
        yield session

    # Патчим на время теста
    with patch("src.server.database.connection.get_db", override_get_db):
        yield session

    # Откатываем транзакцию и закрываем соединение
    session.close()
    transaction.rollback()
    connection.close()


# ============================================
# TEST REDIS SETUP (in-memory dummy)
# ============================================


class DummyRedisClient:
    """Простейший in-memory Redis-заменитель для тестов.

    Достаточно реализовать flushdb и connection_pool.connection_kwargs["host"],
    так как только это используется в текущих тестах.
    """

    def __init__(self):
        self._store = {}
        # Минимальный объект с полем connection_kwargs["host"]
        self.connection_pool = type(
            "Pool", (), {"connection_kwargs": {"host": "localhost"}}
        )()

    def flushdb(self):
        self._store.clear()


@pytest.fixture
def redis_client():
    """In-memory Redis-подобный клиент без подключения к реальному Redis."""
    client = DummyRedisClient()
    # Очищаем "БД" перед тестом
    client.flushdb()

    yield client

    # Очищаем после теста
    client.flushdb()


# ============================================
# FASTAPI TEST CLIENT
# ============================================


@pytest.fixture
def test_client(db_session, redis_client):
    """FastAPI TestClient с переопределенными зависимостями"""

    def override_get_db():
        yield db_session

    # Переопределяем зависимости для тестов
    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Не следуем автоматически за редиректами, чтобы можно было проверять 3xx коды
    with TestClient(fastapi_app, follow_redirects=False) as client:
        yield client

    # Очищаем переопределения
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(test_client, db_session):
    """TestClient с аутентифицированным пользователем"""
    # Создаем тестового пользователя
    user = create_test_user(db_session)

    def override_get_current_user():
        return user

    fastapi_app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )

    yield test_client

    # Очистка
    fastapi_app.dependency_overrides.pop(get_current_user, None)


# ============================================
# TEST DATA HELPERS
# ============================================

fake = Faker()


def create_test_user(db_session, **overrides):
    """Создать тестового пользователя в БД"""
    from src.server.database.models import User
    from src.server.auth.security import get_password_hash

    # Поддерживаем старый параметр is_superuser, маппя его на is_admin
    # в новой модели пользователя.
    is_superuser = overrides.pop("is_superuser", None)
    if is_superuser is not None and "is_admin" not in overrides:
        overrides["is_admin"] = bool(is_superuser)

    user_data = {
        "email": fake.email(),
        "username": fake.user_name(),
        "hashed_password": get_password_hash("password123"),
        "is_active": True,
        "created_at": datetime.utcnow(),
        **overrides,
    }

    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_player(db_session, user_id, **overrides):
    """Создать тестового игрока в БД"""
    from src.server.models.player import Player

    player_data = {
        "user_id": user_id,
        "faceit_id": fake.uuid4(),
        "nickname": fake.user_name(),
        "country": fake.country_code(),
        "skill_level": fake.random_int(min=1, max=10),
        "faceit_elo": fake.random_int(min=800, max=2000),
        "created_at": datetime.utcnow(),
        **overrides,
    }

    player = Player(**player_data)
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    return player


def create_test_analysis(db_session, player_id, **overrides):
    """Создать тестовый анализ в БД"""
    from src.server.models.analysis import Analysis

    analysis_data = {
        "player_id": player_id,
        "analysis_type": "comprehensive",
        "ai_model": "groq",
        "analysis_data": {
            "strengths": ["Good aim", "Good positioning"],
            "weaknesses": ["Communication", "Economy"],
            "recommendations": ["Improve teamwork", "Focus on utility"],
        },
        "created_at": datetime.utcnow(),
        **overrides,
    }

    analysis = Analysis(**analysis_data)
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


# ============================================
# TEST FIXTURES WITH DATA
# ============================================


@pytest.fixture
def test_user(db_session):
    """Создать тестового пользователя"""
    return create_test_user(db_session)


@pytest.fixture
def test_player(db_session, test_user):
    """Создать тестового игрока"""
    return create_test_player(db_session, test_user.id)


@pytest.fixture
def test_analysis(db_session, test_player):
    """Создать тестовый анализ"""
    return create_test_analysis(db_session, test_player.id)


# ============================================
# AUTHENTICATION HELPERS
# ============================================


@pytest.fixture
def auth_headers(test_client, test_user):
    """Заголовки для аутентифицированного пользователя"""
    # Логиним пользователя
    response = test_client.post(
        "/api/auth/login",
        json={
            "email": test_user.email,
            "password": "password123",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    """Создать администратора"""
    return create_test_user(
        db_session,
        is_superuser=True,
        username="admin",
    )


@pytest.fixture
def admin_auth_headers(test_client, admin_user):
    """Заголовки для администратора"""
    response = test_client.post(
        "/api/auth/login",
        json={
            "email": admin_user.email,
            "password": "password123",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================
# MOCK EXTERNAL APIs
# ============================================


@pytest.fixture
def mock_faceit_api():
    """Мок Faceit API с фикстурами для разных сценариев"""
    with patch(
        "src.server.integrations.faceit_client.FaceitClient.get_player"
    ) as mock_get_player, patch(
        "src.server.integrations.faceit_client.FaceitClient.get_player_stats"
    ) as mock_get_stats, patch(
        "src.server.integrations.faceit_client.FaceitClient.get_player_history"
    ) as mock_get_history:

        # Настраиваем мок успешных ответов по умолчанию
        mock_get_player.return_value = {
            "player_id": "test-player-123",
            "nickname": "test_player",
            "country": "RU",
            "games": {"cs2": {"skill_level": 7, "faceit_elo": 1500}},
        }

        mock_get_stats.return_value = {
            "lifetime": {
                "matches": "150",
                "k_d_ratio": "1.25",
                "average_kdr": "1.25",
                "win_rate": "54.67",
                "wins": "82",
            }
        }

        mock_get_history.return_value = {
            "items": [
                {
                    "match_id": "test-match-1",
                    "started_at": 1699876543,
                    "finished_at": 1699880000,
                    "results": {"winner": "faction1"},
                    "teams": {
                        "faction1": {"players": []},
                        "faction2": {"players": []},
                    },
                }
            ]
        }

        yield {
            "get_player": mock_get_player,
            "get_stats": mock_get_stats,
            "get_history": mock_get_history,
        }


@pytest.fixture
def mock_groq_api():
    """Мок Groq API"""
    with patch("src.server.ai.groq_service.GroqService.analyze_player") as mock_analyze:
        mock_analyze.return_value = {
            "analysis": "Тестировочный анализ игрока...",
            "recommendations": ["Тестовая рекомендация 1", "Тестовая рекомендация 2"],
            "strengths": ["Тестовая сила 1", "Тестовая сила 2"],
            "weaknesses": ["Тестовая слабость 1"],
            "rating": 7.5,
        }
        yield mock_analyze


# ============================================
# CELERY TASK HELPERS
# ============================================


@pytest.fixture
def celery_config():
    """Конфигурация для тестирования Celery задач"""
    return {
        "broker_url": "memory://",
        "result_backend": "memory://",
        "task_eager": True,  # Выполнять задачи синхронно
    }


# ============================================
# SETTINGS OVERRIDE
# ============================================


@pytest.fixture
def test_settings(redis_client):
    """Переопределенные настройки для тестов"""
    settings = Settings()
    settings.REDIS_URL = redis_client.connection_pool.connection_kwargs["host"]
    settings.ENVIRONMENT = "test"
    settings.DEBUG = True
    return settings


# ============================================
# CLEANUP START
# ============================================


@pytest.fixture(autouse=True)
def cleanup(db_session, redis_client):
    """Автоматическая очистка данных после каждого теста"""
    yield
    # Очищаем БД (если используем rollback - это не нужно)
    # Очищаем Redis
    redis_client.flushdb()
