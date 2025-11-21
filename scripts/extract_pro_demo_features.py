from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence

from src.server.database.connection import SessionLocal
from src.server.database.models import DemoFeature, ProDemo, ProDemoStatus
from src.ml.features.pro_demo_extractor import extract_player_feature_rows


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(
        description=(
            "Extract basic per-player features from downloaded pro demos "
            "and populate the demo_features table."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of pro_demos to process in one run.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="pro",
        help="Source label to store in DemoFeature.source (e.g. 'pro').",
    )
    return parser


def process_pro_demos(limit: int, source: str) -> None:
    db = SessionLocal()

    try:
        demos: Sequence[ProDemo] = (
            db.query(ProDemo)
            .filter(ProDemo.status == ProDemoStatus.DOWNLOADED)
            .filter(~ProDemo.features.any())
            .order_by(ProDemo.id.asc())
            .limit(limit)
            .all()
        )

        if not demos:
            print("No downloaded pro_demos without features found")
            return

        processed = 0
        failed = 0

        for demo in demos:
            if not demo.storage_path:
                print(f"Skipping demo {demo.id}: no storage_path")
                continue

            demo_path = Path(demo.storage_path)
            if not demo_path.is_file():
                print(f"Skipping demo {demo.id}: file not found at {demo_path}")
                demo.status = ProDemoStatus.FAILED
                db.commit()
                failed += 1
                continue

            print(f"Extracting features from demo {demo.id} ({demo_path})...")

            try:
                rows = extract_player_feature_rows(demo_path)
            except Exception as exc:
                print(f"  Failed to extract features: {exc}")
                demo.status = ProDemoStatus.FAILED
                db.commit()
                failed += 1
                continue

            if not rows:
                print("  No players/features extracted")
                demo.status = ProDemoStatus.FAILED
                db.commit()
                failed += 1
                continue

            for row in rows:
                feature = DemoFeature(
                    pro_demo_id=demo.id,
                    source=source,
                    **row,
                )
                db.add(feature)

            demo.status = ProDemoStatus.PARSED
            db.commit()
            processed += 1
            print(f"  Saved {len(rows)} feature rows")

        print(f"Finished: processed={processed}, failed={failed}")

    finally:
        db.close()


def main() -> None:
    parser = parse_args()
    args = parser.parse_args()

    process_pro_demos(limit=args.limit, source=args.source)


if __name__ == "__main__":
    main()
