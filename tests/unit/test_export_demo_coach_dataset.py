from pathlib import Path
from typing import Any, List, Tuple

import pytest

from scripts import export_demo_coach_dataset as export_script


class DummyDemoAnalyzer:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, str]] = []

    async def analyze_demo(self, upload_file: Any, language: str = "ru") -> str:
        # Store filename and language for assertions
        self.calls.append((upload_file.filename, language))
        # Return a simple marker object that build_training_sample_from_demo will receive
        return f"analysis_for_{upload_file.filename}"


@pytest.mark.asyncio
async def test_analyze_demos_and_export_uses_analyzer_and_writes_samples(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Prepare a couple of fake demo files
    demo1 = tmp_path / "player1_match1.dem"
    demo2 = tmp_path / "player2_match2.dem"
    demo1.write_bytes(b"demo1")
    demo2.write_bytes(b"demo2")

    demo_paths = [demo1, demo2]
    output_path = tmp_path / "output.jsonl"

    # Set up dummy analyzer instance and replace DemoAnalyzer factory in the script
    dummy_analyzer = DummyDemoAnalyzer()

    def _dummy_factory() -> DummyDemoAnalyzer:
        return dummy_analyzer

    monkeypatch.setattr(export_script, "DemoAnalyzer", _dummy_factory)

    # Capture calls to build_training_sample_from_demo and append_samples_to_jsonl
    received_analyses: List[str] = []
    received_samples: List[str] = []
    received_path: list[Path] = []

    def fake_build_training_sample_from_demo(analysis: Any) -> str:
        received_analyses.append(analysis)
        return f"sample_for_{analysis}"

    def fake_append_samples_to_jsonl(samples: Any, path: Path) -> Path:
        # Convert to list in case it's another iterable type
        received_samples.extend(list(samples))
        received_path.append(path)
        return path

    monkeypatch.setattr(
        export_script,
        "build_training_sample_from_demo",
        fake_build_training_sample_from_demo,
    )
    monkeypatch.setattr(
        export_script,
        "append_samples_to_jsonl",
        fake_append_samples_to_jsonl,
    )

    # Run the async export function
    await export_script.analyze_demos_and_export(
        demo_paths=demo_paths,
        output=output_path,
        language="en",
    )

    # DemoAnalyzer should be called once per demo file with correct filenames and language
    assert dummy_analyzer.calls == [
        ("player1_match1.dem", "en"),
        ("player2_match2.dem", "en"),
    ]

    # build_training_sample_from_demo should receive analyses returned by DummyDemoAnalyzer
    assert received_analyses == [
        "analysis_for_player1_match1.dem",
        "analysis_for_player2_match2.dem",
    ]

    # append_samples_to_jsonl should be called once with all samples and the target path
    assert received_path == [output_path]
    assert received_samples == [
        "sample_for_analysis_for_player1_match1.dem",
        "sample_for_analysis_for_player2_match2.dem",
    ]
