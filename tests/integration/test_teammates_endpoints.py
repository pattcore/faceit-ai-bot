import pytest
from unittest.mock import Mock, AsyncMock

from src.server.database.models import TeammateProfile as TeammateProfileDB
from src.server.features.teammates.routes import teammate_service


@pytest.fixture
def mock_teammates_dependencies():
    """Mock AI and Faceit clients used inside global teammate_service instance."""
    mock_ai = Mock()
    mock_ai.describe_teammate_matches = AsyncMock(return_value={})
    teammate_service.ai = mock_ai

    mock_faceit = Mock()
    mock_faceit.get_player_by_nickname = AsyncMock(return_value=None)
    teammate_service.faceit_client = mock_faceit

    yield {"ai": mock_ai, "faceit": mock_faceit}


@pytest.mark.integration
def test_update_teammate_preferences_endpoint(authenticated_client, db_session):
    payload = {
        "min_elo": 1000,
        "max_elo": 2000,
        "preferred_maps": ["mirage"],
        "preferred_roles": ["rifler"],
        "communication_lang": ["ru"],
        "play_style": "aggressive",
        "time_zone": "UTC",
        "about": "About me",
        "availability": "Evenings",
        "discord_contact": "discord#1234",
        "telegram_contact": "@user",
        "contact_url": "https://example.com",
    }

    response = authenticated_client.put("/teammates/preferences", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["preferred_roles"] == ["rifler"]
    assert data["communication_lang"] == ["ru"]
    assert data["preferred_maps"] == ["mirage"]

    profiles = db_session.query(TeammateProfileDB).all()
    assert len(profiles) == 1
    profile = profiles[0]

    assert profile.roles == "rifler"
    assert profile.languages == "ru"
    assert profile.preferred_maps == "mirage"
    assert profile.play_style == "aggressive"
    assert profile.about == "About me"
    assert profile.availability == "Evenings"
    assert profile.discord_contact == "discord#1234"
    assert profile.telegram_contact == "@user"
    assert profile.contact_url == "https://example.com"


@pytest.mark.integration
def test_teammates_search_returns_demo_profile_when_no_candidates(
    authenticated_client,
    db_session,
    mock_teammates_dependencies,
):
    payload = {
        "min_elo": 1000,
        "max_elo": 1500,
        "preferred_maps": ["mirage"],
        "preferred_roles": ["rifler"],
        "communication_lang": ["en"],
        "play_style": "aggressive",
        "time_zone": "UTC",
        "about": None,
        "availability": None,
        "discord_contact": None,
        "telegram_contact": None,
        "contact_url": None,
    }

    response = authenticated_client.post("/teammates/search", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    profile = data[0]
    assert profile["stats"]["faceit_elo"] == 1500
    assert profile["preferences"]["preferred_roles"] == ["rifler"]
    assert profile["preferences"]["preferred_maps"] == ["mirage"]


@pytest.mark.integration
def test_teammates_search_uses_existing_candidate_profile(
    authenticated_client,
    db_session,
    mock_teammates_dependencies,
):
    from src.server.database.models import TeammateProfile as TeammateProfileDB

    current_user_profile_count = db_session.query(TeammateProfileDB).count()

    other_profile = TeammateProfileDB(
        user_id=9999,
        faceit_nickname="Candidate",
        elo=1700,
        level=9,
        roles="rifler",
        languages="en",
        preferred_maps="mirage",
        play_style="aggressive",
    )
    db_session.add(other_profile)
    db_session.commit()

    payload = {
        "min_elo": 1600,
        "max_elo": 1800,
        "preferred_maps": ["mirage"],
        "preferred_roles": ["rifler"],
        "communication_lang": ["en"],
        "play_style": "aggressive",
        "time_zone": "UTC",
        "about": None,
        "availability": None,
        "discord_contact": None,
        "telegram_contact": None,
        "contact_url": None,
    }

    response = authenticated_client.post("/teammates/search", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    profile = data[0]
    assert profile["stats"]["faceit_elo"] == 1700
    assert profile["preferences"]["preferred_roles"] == ["rifler"]
    assert profile["preferences"]["preferred_maps"] == ["mirage"]

    assert db_session.query(TeammateProfileDB).count() == current_user_profile_count + 1
