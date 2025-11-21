"""Entry point for training ML models related to demo coaching.

This script is intentionally lightweight and does not import heavy
frameworks (PyTorch, etc.). Use it as a CLI wrapper that delegates
training logic to functions under src.ml.* in a separate ML environment.
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from src.ml.models import train_demo_coach


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(
        description=(
            "Train demo coaching models on prepared datasets. "
            "This is a thin CLI wrapper; put heavy ML code under src.ml.*."
        )
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help=(
            "Path to prepared JSONL dataset (e.g. "
            "data/demo_coach_ru_stub_prompts.jsonl)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to store trained model checkpoints and logs.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Optional path to a training config file (YAML/JSON).",
    )
    return parser


def main() -> None:
    parser = parse_args()
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)

    if not dataset_path.is_file():
        raise SystemExit(f"Dataset file not found: {dataset_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("[train.py] Dataset:", dataset_path)
    print("[train.py] Output dir:", output_dir)
    if args.config:
        print("[train.py] Config:", args.config)

    # Delegate to lightweight training helper. Real ML training can build on
    # top of this in a dedicated environment.
    train_demo_coach(
        dataset_path=dataset_path,
        output_dir=output_dir,
        config_path=args.config,
    )


if __name__ == "__main__":
    main()
