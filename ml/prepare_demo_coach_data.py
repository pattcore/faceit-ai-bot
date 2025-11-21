from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Dict
import json
import sys

from src.server.features.demo_analyzer.models import DemoTrainingSample


def build_prompt(sample: DemoTrainingSample) -> str:
    input_data: Dict[str, Any] = sample.input.model_dump()
    language = input_data.get("language", "ru")

    if language == "ru":
        header = (
            "Ты — AI‑тренер по CS2. На входе у тебя структурированные данные матча "
            "(JSON ниже). На их основе составь развёрнутый коуч‑отчёт для игрока "
            "в формате JSON со следующей схемой: overview, strengths, weaknesses, "
            "key_moments, training_plan, summary.\n\n"
            "Входные данные:\n"
        )
    else:
        header = (
            "You are an AI CS2 coach. You receive structured match data (JSON below). "
            "Based on it, generate a detailed coaching report for the player in JSON "
            "with the following schema: overview, strengths, weaknesses, "
            "key_moments, training_plan, summary.\n\n"
            "Input data:\n"
        )

    json_input = json.dumps(input_data, ensure_ascii=False, indent=2)
    return header + json_input


def build_completion(sample: DemoTrainingSample) -> str:
    return sample.output.model_dump_json(ensure_ascii=False)


def prepare_dataset(input_path: Path, output_path: Path) -> None:
    total = 0
    written = 0

    with input_path.open("r", encoding="utf-8") as fin, output_path.open(
        "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue

            total += 1
            try:
                sample = DemoTrainingSample.model_validate_json(line)
            except Exception as exc:
                print(f"Skipping line {total}: parse error: {exc}", file=sys.stderr)
                continue

            if sample.output is None:
                continue

            prompt = build_prompt(sample)
            completion = build_completion(sample)

            record = {
                "prompt": prompt,
                "completion": completion,
                "language": sample.input.language,
                "source": sample.source,
                "created_at": sample.created_at.isoformat(),
            }
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    print(f"Read {total} samples, wrote {written} training records to {output_path}")


def main() -> None:
    parser = ArgumentParser(
        description=(
            "Convert DemoTrainingSample JSONL into prompt/completion JSONL "
            "for LLM training"
        )
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to JSONL file with DemoTrainingSample objects",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to JSONL file to write prompt/completion pairs to",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        raise SystemExit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepare_dataset(input_path, output_path)


if __name__ == "__main__":
    main()
