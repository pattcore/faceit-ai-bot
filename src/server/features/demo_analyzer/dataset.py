from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import CoachReport, DemoAnalysis, DemoAnalysisInput, DemoTrainingSample


def build_training_sample_from_demo(
    demo: DemoAnalysis,
    source: str = "demo_analyzer_stub",
) -> DemoTrainingSample:
    """Build a training sample (input/output pair) from a DemoAnalysis object.

    Requires that demo.demo_input and demo.coach_report are populated.
    """
    if demo.demo_input is None:
        raise ValueError("DemoAnalysis.demo_input is required to build a training sample")
    if demo.coach_report is None:
        raise ValueError("DemoAnalysis.coach_report is required to build a training sample")

    if isinstance(demo.demo_input, DemoAnalysisInput):
        input_obj = demo.demo_input
    else:
        input_obj = DemoAnalysisInput.model_validate(demo.demo_input)

    if isinstance(demo.coach_report, CoachReport):
        output_obj = demo.coach_report
    else:
        output_obj = CoachReport.model_validate(demo.coach_report)

    return DemoTrainingSample(
        input=input_obj,
        output=output_obj,
        source=source,
        created_at=datetime.utcnow(),
    )


def append_samples_to_jsonl(
    samples: Iterable[DemoTrainingSample],
    path: str | Path,
) -> Path:
    """Append training samples to a JSONL file on disk.

    Each line is a UTF-8 JSON object produced by pydantic's model_dump_json.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("a", encoding="utf-8") as f:
        for sample in samples:
            f.write(sample.model_dump_json(ensure_ascii=False) + "\n")

    return target
