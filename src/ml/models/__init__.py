"""Model architectures and wrappers for demo coaching and related tasks.

This module intentionally avoids importing heavy ML frameworks (PyTorch,
Transformers, etc.). It can be used from lightweight environments to
inspect datasets and orchestrate training that happens elsewhere.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Optional
import json


def train_demo_coach(
    dataset_path: Path | str,
    output_dir: Path | str,
    config_path: Optional[Path | str] = None,
) -> None:
    """Lightweight helper for demo coach training.

    This function does **not** perform real model training. Instead, it
    validates that the dataset is readable, computes simple statistics
    (number of samples, language and source distribution) and writes a
    ``training_summary.json`` file to the output directory.

    Heavyweight training logic (PyTorch / Transformers) should live in a
    dedicated ML environment and can import this function as a first
    validation step.
    """

    ds_path = Path(dataset_path)
    out_dir = Path(output_dir)

    if not ds_path.is_file():
        raise FileNotFoundError(f"Dataset file not found: {ds_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    languages: Counter[str] = Counter()
    sources: Counter[str] = Counter()

    with ds_path.open("r", encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue

            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                # Skip malformed lines but keep counting total
                continue

            lang = str(obj.get("language") or "unknown")
            src = str(obj.get("source") or "unknown")
            languages[lang] += 1
            sources[src] += 1

    summary = {
        "dataset_path": str(ds_path),
        "total_samples": total,
        "languages": dict(languages),
        "sources": dict(sources),
        "config_path": str(config_path) if config_path is not None else None,
    }

    summary_path = out_dir / "training_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[train_demo_coach] Dataset:", ds_path)
    print("[train_demo_coach] Total samples:", total)
    print("[train_demo_coach] Languages:", dict(languages))
    print("[train_demo_coach] Sources:", dict(sources))
    print("[train_demo_coach] Summary written to:", summary_path)

