from typing import Any, Dict

import pytest

from src.server.ai.groq_service import GroqService
from src.server.config.settings import settings


pytestmark = pytest.mark.asyncio


def _force_remote_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LOCAL_LLM_BASE_URL", None, raising=False)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODEL", None, raising=False)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None, raising=False)
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", None, raising=False)
    monkeypatch.setattr(settings, "GROQ_API_KEY", None, raising=False)


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
