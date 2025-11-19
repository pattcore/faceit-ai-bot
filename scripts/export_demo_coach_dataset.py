import asyncio
import json
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from src.server.features.demo_analyzer.dataset import (
    append_samples_to_jsonl,
    build_training_sample_from_demo,
)
from src.server.features.demo_analyzer.service import DemoAnalyzer


async def analyze_demos_and_export(
    demo_paths: List[Path],
    output: Path,
    language: str = "ru",
) -> None:
    analyzer = DemoAnalyzer()

    samples = []
    for demo_path in demo_paths:
        print(f"Analyzing {demo_path}...")
        with demo_path.open("rb") as f:
            from fastapi import UploadFile

            upload = UploadFile(filename=demo_path.name, file=f)  # type: ignore[arg-type]
            analysis = await analyzer.analyze_demo(upload, language=language)

        sample = build_training_sample_from_demo(analysis)
        samples.append(sample)

    append_samples_to_jsonl(samples, output)
    print(f"Wrote {len(samples)} samples to {output}")


def main() -> None:
    parser = ArgumentParser(description="Export demo coach training dataset from .dem files")
    parser.add_argument("--demos", type=str, required=True, help="Path to folder with .dem files")
    parser.add_argument("--output", type=str, required=True, help="Path to JSONL file to write samples to")
    parser.add_argument("--language", type=str, default="ru", help="Target language for coach reports (ru/en)")

    args = parser.parse_args()
    demo_dir = Path(args.demos)
    output_path = Path(args.output)

    demo_files = sorted(p for p in demo_dir.glob("*.dem") if p.is_file())
    if not demo_files:
        print(f"No .dem files found in {demo_dir}")
        return

    asyncio.run(analyze_demos_and_export(demo_files, output_path, language=args.language))


if __name__ == "__main__":
    main()
