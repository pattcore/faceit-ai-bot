from typing import Any, Dict
import json

import pytest

import src.server.ai.groq_service as groq_module
from src.server.ai.groq_service import GroqService
from src.server.config.settings import settings


pytestmark = pytest.mark.asyncio


def _force_remote_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LOCAL_LLM_BASE_URL", None, raising=False)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODEL", None, raising=False)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None, raising=False)
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", None, raising=False)
    monkeypatch.setattr(settings, "GROQ_API_KEY", None, raising=False)


def _force_openrouter(
    monkeypatch: pytest.MonkeyPatch,
    api_key: str = "test-openrouter-key",
) -> None:
    monkeypatch.setattr(settings, "LOCAL_LLM_BASE_URL", None, raising=False)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODEL", None, raising=False)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", api_key, raising=False)
    monkeypatch.setattr(
        settings,
        "OPENROUTER_MODEL",
        "test/openrouter-model",
        raising=False,
    )
    monkeypatch.setattr(settings, "GROQ_API_KEY", None, raising=False)


class DummyResponse:
    def __init__(
        self,
        status: int = 200,
        json_data: Dict[str, Any] | None = None,
        text_data: str = "",
    ) -> None:
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data

    async def __aenter__(self) -> "DummyResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def json(self) -> Dict[str, Any]:
        return self._json_data

    async def text(self) -> str:
        return self._text_data


class DummySession:
    def __init__(self, response: DummyResponse) -> None:
        self._response = response
        self.last_url: str | None = None
        self.last_headers: Dict[str, Any] | None = None
        self.last_json: Dict[str, Any] | None = None

    async def __aenter__(self) -> "DummySession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def post(
        self,
        url: str,
        *,
        headers: Dict[str, Any] | None = None,
        json: Dict[str, Any] | None = None,
    ) -> DummyResponse:
        self.last_url = url
        self.last_headers = headers
        self.last_json = json
        return self._response


class TestGroqServiceHelpers:
    def test_normalize_language_and_default_training_plan(self) -> None:
        service = GroqService(api_key="dummy")

        assert service._normalize_language(None) == "ru"
        assert service._normalize_language("ru") == "ru"
        assert service._normalize_language("RU-ru") == "ru"
        assert service._normalize_language("en") == "en"
        assert service._normalize_language("EN-us") == "en"
        assert service._normalize_language("de") == "en"

        plan_ru = service._get_default_training_plan("ru")
        plan_en = service._get_default_training_plan("en")

        for plan in (plan_ru, plan_en):
            assert isinstance(plan, dict)
            assert "focus_areas" in plan
            assert "daily_exercises" in plan
            assert "estimated_time" in plan

    def test_build_analysis_prompt_includes_extra_context(self) -> None:
        service = GroqService(api_key="dummy")
        stats: Dict[str, Any] = {
            "kd_ratio": 1.2,
            "hs_percentage": 55,
            "win_rate": 60,
            "avg_damage": 80,
            "matches_played": 100,
            "map_name": "de_inferno",
            "total_rounds": 30,
            "score_team1": 16,
            "score_team2": 14,
            "key_moments": [
                {"round": 10, "description": "clutch 1v2"},
                {"round": 25, "description": "multi-kill on A site"},
            ],
        }

        prompt_ru = service._build_analysis_prompt(stats, match_history=[], language="ru")
        prompt_en = service._build_analysis_prompt(stats, match_history=[], language="en")

        assert "de_inferno" in prompt_ru
        assert "de_inferno" in prompt_en
        assert "Ключевые раунды" in prompt_ru
        assert "Key rounds" in prompt_en


class TestGroqServiceWithoutApiKey:
    async def test_analyze_player_performance_without_api_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_remote_without_key(monkeypatch)
        service = GroqService(api_key=None)

        assert getattr(service, "provider") != "local"
        assert service.api_key is None

        result = await service.analyze_player_performance(
            stats={
                "kd_ratio": 1.0,
                "win_rate": 50.0,
                "hs_percentage": 40.0,
                "matches_played": 10,
            },
            match_history=[],
            language="ru",
        )

        assert "Analysis unavailable" in result

    async def test_generate_demo_coach_report_without_api_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_remote_without_key(monkeypatch)
        service = GroqService(api_key=None)

        report = await service.generate_demo_coach_report(
            demo_input={"match_id": "123", "players": []},
            language="ru",
        )

        assert report == {}

    async def test_generate_training_plan_without_api_key_returns_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_remote_without_key(monkeypatch)
        service = GroqService(api_key=None)

        result = await service.generate_training_plan(
            player_stats={
                "kd_ratio": 1.0,
                "win_rate": 50.0,
                "hs_percentage": 40.0,
            },
            focus_areas=["aim"],
            language="ru",
        )

        assert isinstance(result, dict)
        assert "daily_exercises" in result
        assert result["daily_exercises"]
        assert "estimated_time" in result

    async def test_describe_teammate_matches_without_api_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_remote_without_key(monkeypatch)
        service = GroqService(api_key=None)

        result = await service.describe_teammate_matches(
            payload={"player": {"id": "p1"}, "candidates": []},
            language="ru",
        )

        assert result == {}


class TestGroqServiceWithHttpMock:
    async def test_analyze_player_performance_success_openrouter_headers(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_openrouter(monkeypatch, api_key="test-openrouter-key")
        monkeypatch.setattr(
            settings,
            "WEBSITE_URL",
            "https://example.com",
            raising=False,
        )
        monkeypatch.setattr(
            settings,
            "APP_TITLE",
            "Test App",
            raising=False,
        )

        response_json: Dict[str, Any] = {
            "choices": [
                {"message": {"content": "analysis result"}},
            ],
        }
        dummy_response = DummyResponse(status=200, json_data=response_json)
        dummy_session = DummySession(dummy_response)

        monkeypatch.setattr(
            groq_module.aiohttp,
            "ClientSession",
            lambda: dummy_session,
        )

        service = GroqService(api_key=None)

        result = await service.analyze_player_performance(
            stats={
                "kd_ratio": 1.0,
                "win_rate": 60.0,
                "hs_percentage": 40.0,
                "matches_played": 20,
            },
            match_history=[],
            language="en",
        )

        assert "analysis result" in result
        assert dummy_session.last_url == service.groq_base_url
        assert dummy_session.last_headers is not None
        assert dummy_session.last_headers.get("Authorization") == (
            "Bearer test-openrouter-key"
        )
        assert dummy_session.last_headers.get("HTTP-Referer") == "https://example.com"
        assert dummy_session.last_headers.get("X-Title") == "Test App"
        assert dummy_session.last_json is not None
        assert dummy_session.last_json.get("model") == service.model

    async def test_analyze_player_performance_http_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_openrouter(monkeypatch, api_key="test-openrouter-key")
        dummy_response = DummyResponse(status=500, text_data="server error")
        dummy_session = DummySession(dummy_response)

        monkeypatch.setattr(
            groq_module.aiohttp,
            "ClientSession",
            lambda: dummy_session,
        )

        service = GroqService(api_key=None)

        result = await service.analyze_player_performance(
            stats={},
            match_history=[],
            language="en",
        )

        assert result == "Error analyzing performance: 500"

    async def test_generate_demo_coach_report_success_with_code_fences(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_openrouter(monkeypatch, api_key="demo-key")

        report_body: Dict[str, Any] = {
            "overview": "ok",
            "strengths": [],
            "weaknesses": [],
            "key_moments": [],
            "training_plan": {},
            "summary": "done",
        }
        fenced_content = "```json\n" + json.dumps(report_body) + "\n```"

        dummy_response = DummyResponse(
            status=200,
            json_data={
                "choices": [
                    {"message": {"content": fenced_content}},
                ],
            },
        )
        dummy_session = DummySession(dummy_response)

        monkeypatch.setattr(
            groq_module.aiohttp,
            "ClientSession",
            lambda: dummy_session,
        )

        service = GroqService(api_key=None)

        result = await service.generate_demo_coach_report(
            demo_input={"match_id": "123", "players": []},
            language="en",
        )

        assert result == report_body

    async def test_generate_training_plan_success_parses_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_openrouter(monkeypatch, api_key="plan-key")

        plan_body: Dict[str, Any] = {
            "daily_exercises": [
                {"name": "aim", "duration": "30m", "description": "do aim"},
            ],
            "weekly_goals": ["improve aim"],
            "estimated_time": "4 weeks",
        }
        content = json.dumps(plan_body)

        dummy_response = DummyResponse(
            status=200,
            json_data={
                "choices": [
                    {"message": {"content": content}},
                ],
            },
        )
        dummy_session = DummySession(dummy_response)

        monkeypatch.setattr(
            groq_module.aiohttp,
            "ClientSession",
            lambda: dummy_session,
        )

        service = GroqService(api_key=None)

        result = await service.generate_training_plan(
            player_stats={"kd_ratio": 1.0},
            focus_areas=["aim"],
            language="en",
        )

        assert result == plan_body

    async def test_describe_teammate_matches_success_parses_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _force_openrouter(monkeypatch, api_key="team-key")

        body: Dict[str, Any] = {
            "candidate1": {
                "score": 0.9,
                "summary": "good fit",
            },
        }
        content = json.dumps(body)

        dummy_response = DummyResponse(
            status=200,
            json_data={
                "choices": [
                    {"message": {"content": content}},
                ],
            },
        )
        dummy_session = DummySession(dummy_response)

        monkeypatch.setattr(
            groq_module.aiohttp,
            "ClientSession",
            lambda: dummy_session,
        )

        service = GroqService(api_key=None)

        result = await service.describe_teammate_matches(
            payload={"player": {"id": "p1"}, "candidates": []},
            language="en",
        )

        assert result == body
