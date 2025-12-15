import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pytest

from src.server.features.demo_analyzer.dataset import (
    append_samples_to_jsonl,
    build_training_sample_from_demo,
)
from src.server.features.demo_analyzer.models import (
    CoachReport,
    DemoAnalysis,
    DemoAnalysisInput,
    DemoMetadata,
    DemoTrainingSample,
    PlayerPerformance,
    RoundAnalysis,
)


def _make_default_demo_input() -> DemoAnalysisInput:
    return DemoAnalysisInput(
        language="en",
        player={"id": "p1"},
        match={"id": "m1"},
        aggregate_stats={"kills": 10},
        flags=["test"],
        key_rounds=[{"round": 1}],
    )


def _make_default_coach_report() -> CoachReport:
    return CoachReport(
        overview="overview",
        strengths=[{"area": "aim"}],
        weaknesses=[{"area": "positioning"}],
        key_moments=[{"round": 1}],
        training_plan=[{"task": "dm"}],
        summary="summary",
    )


def _make_demo_analysis(
    demo_input: DemoAnalysisInput | None,
    coach_report: CoachReport | None,
) -> DemoAnalysis:
    metadata = DemoMetadata(
        match_id="match-1",
        map_name="de_inferno",
        game_mode="5v5",
        date_played=datetime.utcnow(),
        duration=30,
        score={"team1": 16, "team2": 14},
    )

    performance = PlayerPerformance(
        player_id="p1",
        kills=10,
        deaths=5,
        assists=3,
        headshot_percentage=50.0,
        entry_kills=2,
        clutches_won=1,
        damage_per_round=90.0,
        utility_damage=20.0,
        flash_assists=2,
    )

    round_analysis = [
        RoundAnalysis(
            round_number=1,
            winner_side="CT",
            winner_team="team1",
            round_type="full-buy",
            key_events=[],
            player_performances={"p1": performance},
        )
    ]

    return DemoAnalysis(
        demo_id="demo-1",
        metadata=metadata,
        overall_performance={"p1": performance},
        round_analysis=round_analysis,
        key_moments=[],
        recommendations=["work on spray control"],
        improvement_areas=[{"area": "spray"}],
        coach_report=coach_report,
        demo_input=demo_input,
    )


def test_build_training_sample_from_demo_uses_existing_models() -> None:
    demo_input = _make_default_demo_input()
    coach_report = _make_default_coach_report()
    demo = _make_demo_analysis(demo_input=demo_input, coach_report=coach_report)

    sample = build_training_sample_from_demo(demo, source="from_test")

    assert isinstance(sample, DemoTrainingSample)
    assert sample.input is demo_input
    assert sample.output is coach_report
    assert sample.source == "from_test"
    assert isinstance(sample.created_at, datetime)


def test_build_training_sample_from_demo_accepts_dicts() -> None:
    demo_input = _make_default_demo_input()
    coach_report = _make_default_coach_report()
    demo = _make_demo_analysis(demo_input=None, coach_report=None)

    # Simulate a DemoAnalysis instance loaded with raw dicts for nested fields.
    # These assignments intentionally bypass the static type of the attributes
    # to mimic how data might look when loaded from an external JSON source.
    demo.demo_input = cast(Any, demo_input.model_dump())
    demo.coach_report = cast(Any, coach_report.model_dump())

    sample = build_training_sample_from_demo(demo, source="dict_source")

    assert isinstance(sample.input, DemoAnalysisInput)
    assert isinstance(sample.output, CoachReport)
    assert sample.source == "dict_source"
    assert sample.input.language == demo_input.language
    assert sample.output.overview == coach_report.overview


def test_build_training_sample_from_demo_requires_demo_input() -> None:
    demo_input = _make_default_demo_input()
    coach_report = _make_default_coach_report()
    demo = _make_demo_analysis(demo_input=demo_input, coach_report=coach_report)

    demo.demo_input = None

    with pytest.raises(ValueError) as exc:
        build_training_sample_from_demo(demo)

    assert "demo_input" in str(exc.value)


def test_build_training_sample_from_demo_requires_coach_report() -> None:
    demo_input = _make_default_demo_input()
    coach_report = _make_default_coach_report()
    demo = _make_demo_analysis(demo_input=demo_input, coach_report=coach_report)

    demo.coach_report = None

    with pytest.raises(ValueError) as exc:
        build_training_sample_from_demo(demo)

    assert "coach_report" in str(exc.value)


def test_append_samples_to_jsonl_writes_one_line_per_sample(tmp_path: Path) -> None:
    demo_input = _make_default_demo_input()
    coach_report = _make_default_coach_report()
    demo = _make_demo_analysis(demo_input=demo_input, coach_report=coach_report)

    sample1 = build_training_sample_from_demo(demo, source="s1")
    sample2 = build_training_sample_from_demo(demo, source="s2")

    target = tmp_path / "subdir" / "samples.jsonl"
    result_path = append_samples_to_jsonl([sample1, sample2], target)

    assert result_path == target
    assert target.exists()

    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    objs = [json.loads(line) for line in lines]
    assert {obj["source"] for obj in objs} == {"s1", "s2"}

    for obj in objs:
        assert "input" in obj
        assert "output" in obj
        assert "created_at" in obj
