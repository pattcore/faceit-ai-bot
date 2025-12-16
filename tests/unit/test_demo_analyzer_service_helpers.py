from typing import Any, Dict, List

from src.server.features.demo_analyzer.models import DemoAnalysisInput, PlayerPerformance
from src.server.features.demo_analyzer.service import DemoAnalyzer


def _make_demo_analyzer() -> DemoAnalyzer:
    """Create DemoAnalyzer instance without running heavy __init__ (Groq, Faceit)."""
    return DemoAnalyzer.__new__(DemoAnalyzer)


def test_build_demo_analysis_input_populates_fields_and_flags() -> None:
    analyzer = _make_demo_analyzer()

    demo_data: Dict[str, Any] = {
        "main_player": "PlayerOne",
        "map": "de_inferno",
        "score": {"team1": 16, "team2": 10},
        "total_rounds": 26,
    }

    main_perf = PlayerPerformance(
        player_id="PlayerOne",
        kills=20,
        deaths=10,
        assists=5,
        headshot_percentage=35.0,
        entry_kills=4,
        clutches_won=0,
        damage_per_round=65.0,
        utility_damage=20.0,
        flash_assists=3,
    )
    player_performances = {"PlayerOne": main_perf}

    key_moments: List[Dict[str, Any]] = [
        {"round": 5, "type": "swing_round", "description": "Important mid round"},
        {"round": 10, "type": "eco_mistake", "description": "Lost eco"},
    ]

    result = analyzer._build_demo_analysis_input(
        demo_data=demo_data,
        player_performances=player_performances,
        round_analysis=[],
        key_moments=key_moments,
        language="ru",
    )

    assert isinstance(result, DemoAnalysisInput)
    assert result.language == "ru"
    assert result.player["nickname"] == "PlayerOne"
    assert result.match["map"] == "de_inferno"
    assert result.match["score"] == "16-10"

    agg = result.aggregate_stats
    assert agg["kills"] == 20
    assert agg["deaths"] == 10
    assert agg["assists"] == 5
    assert agg["kd"] == 2.0
    assert agg["adr"] == 65.0
    assert agg["hs_percent"] == 35.0
    assert agg["clutches_won"] == 0

    flags = set(result.flags)
    # With kd=2.0, hs=35.0, adr=65.0, clutches_won=0 and kills>10
    assert "low_headshot_percentage" in flags
    assert "low_damage_per_round" in flags
    assert "weak_clutch_conversion" in flags

    assert len(result.key_rounds) == 2
    first = result.key_rounds[0]
    assert first["round"] == 5
    assert first["situation"] == "swing_round"
    assert first["player_pov"] == ["Important mid round"]


def test_build_demo_analysis_input_without_player_performance_uses_defaults() -> None:
    analyzer = _make_demo_analyzer()

    demo_data: Dict[str, Any] = {
        "main_player": "NoStatsPlayer",
        "map": "de_mirage",
        "score": {"team1": 8, "team2": 16},
        "total_rounds": 24,
    }

    result = analyzer._build_demo_analysis_input(
        demo_data=demo_data,
        player_performances={},
        round_analysis=[],
        key_moments=[],
        language="en",
    )

    assert isinstance(result, DemoAnalysisInput)
    assert result.language == "en"
    assert result.player["nickname"] == "NoStatsPlayer"
    assert result.match["map"] == "de_mirage"
    assert result.match["score"] == "8-16"

    agg = result.aggregate_stats
    assert agg["kills"] == 0
    assert agg["deaths"] == 1
    assert agg["kd"] == 0.0

    flags = set(result.flags)
    # No stats -> low KD and low damage
    assert "low_kd_ratio" in flags
    assert "low_damage_per_round" in flags


def _make_demo_input_with_key_rounds() -> DemoAnalysisInput:
    return DemoAnalysisInput(
        language="ru",
        player={"nickname": "PlayerOne"},
        match={"map": "de_inferno", "score": "16-10"},
        aggregate_stats={},
        flags=[],
        key_rounds=[
            {
                "round": 5,
                "situation": "swing_round",
                "player_pov": ["Won important duel"],
            },
            {
                "round": 10,
                "situation": "eco_mistake",
                "player_pov": ["Lost eco without nades"],
            },
        ],
    )


def test_build_coach_report_stub_uses_stats_and_key_rounds() -> None:
    analyzer = _make_demo_analyzer()
    demo_input = _make_demo_input_with_key_rounds()

    main_perf = PlayerPerformance(
        player_id="PlayerOne",
        kills=24,
        deaths=16,
        assists=6,
        headshot_percentage=45.0,
        entry_kills=5,
        clutches_won=2,
        damage_per_round=80.0,
        utility_damage=25.0,
        flash_assists=4,
    )
    player_performances = {"PlayerOne": main_perf}

    improvement_areas: List[Dict[str, Any]] = []
    recommendations = ["Work on utility usage", "Review your lost rounds"]

    stub = analyzer._build_coach_report_stub(
        demo_input=demo_input,
        player_performances=player_performances,
        improvement_areas=improvement_areas,
        recommendations=recommendations,
        language="ru",
    )

    assert stub["language"] == "ru"
    assert isinstance(stub["overall_score"], float)
    assert "de_inferno" in stub["overview"]
    assert "16-10" in stub["overview"]

    strengths = stub["strengths"]
    weaknesses = stub["weaknesses"]
    assert isinstance(strengths, list)
    assert isinstance(weaknesses, list)
    assert strengths  # non-empty for good stats

    key_moments = stub["key_moments"]
    assert isinstance(key_moments, list)
    assert len(key_moments) >= 1
    assert key_moments[0]["round"] == 5

    # Recommendations should be turned into structured items preserving advice text
    rec_advices = [r["advice"] for r in stub["recommendations"]]
    for rec in recommendations:
        assert rec in rec_advices

    training_plan = stub["training_plan"]
    assert isinstance(training_plan, list)
    assert training_plan  # non-empty when there are weaknesses


def test_build_coach_report_stub_with_weak_stats_produces_weaknesses() -> None:
    analyzer = _make_demo_analyzer()

    demo_input = DemoAnalysisInput(
        language="ru",
        player={"nickname": "PlayerTwo"},
        match={"map": "de_mirage", "score": "8-16"},
        aggregate_stats={},
        flags=[],
        key_rounds=[],
    )

    weak_perf = PlayerPerformance(
        player_id="PlayerTwo",
        kills=5,
        deaths=15,
        assists=2,
        headshot_percentage=20.0,
        entry_kills=0,
        clutches_won=0,
        damage_per_round=40.0,
        utility_damage=10.0,
        flash_assists=1,
    )

    stub = analyzer._build_coach_report_stub(
        demo_input=demo_input,
        player_performances={"PlayerTwo": weak_perf},
        improvement_areas=[],
        recommendations=["Train aim", "Use more headshot-focused drills"],
        language="ru",
    )

    weaknesses = stub["weaknesses"]
    assert isinstance(weaknesses, list)
    assert weaknesses

    titles = {w.get("title") for w in weaknesses}
    # Expect at least one weakness about duels and one about headshots
    assert any("дуэлях" in (t or "") for t in titles)
    assert any("хедшотов" in (t or "") for t in titles)
