from __future__ import annotations

import asyncio
from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence

import aiohttp

from src.server.database.connection import SessionLocal
from src.server.database.models import ProDemo, ProDemoStatus
from src.server.integrations.faceit_client import FaceitAPIClient


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(
        description="Download professional CS2 demos for queued pro_demos records.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/pro_demos",
        help="Directory to store downloaded .dem files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of queued demos to process in one run.",
    )
    return parser


async def download_pending_pro_demos(output_dir: Path, limit: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    client = FaceitAPIClient()

    try:
        demos: Sequence[ProDemo] = (
            db.query(ProDemo)
            .filter(ProDemo.status.in_([ProDemoStatus.QUEUED, ProDemoStatus.DOWNLOADING]))
            .order_by(ProDemo.id.asc())
            .limit(limit)
            .all()
        )

        if not demos:
            print("No queued pro_demos to process")
            return

        async with aiohttp.ClientSession() as session:
            downloaded = 0
            failed = 0

            for demo in demos:
                print(f"Processing match {demo.faceit_match_id}...")
                demo.status = ProDemoStatus.DOWNLOADING
                db.commit()

                try:
                    details = await client.get_match_details(demo.faceit_match_id)
                except Exception as exc:
                    print(f"  Failed to get match details: {exc}")
                    demo.status = ProDemoStatus.FAILED
                    db.commit()
                    failed += 1
                    continue

                if not details:
                    print("  Empty match details response")
                    demo.status = ProDemoStatus.FAILED
                    db.commit()
                    failed += 1
                    continue

                demo_urls = details.get("demo_url") or []
                if not demo_urls:
                    print("  No demo_url found in match details")
                    demo.status = ProDemoStatus.FAILED
                    db.commit()
                    failed += 1
                    continue

                resource_url = demo_urls[0]
                demo.demo_url = resource_url

                filename = resource_url.rstrip("/").split("/")[-1] or f"{demo.faceit_match_id}.dem"
                dest_path = output_dir / filename

                if dest_path.exists():
                    print(f"  File already exists, skipping download: {dest_path}")
                    demo.storage_path = str(dest_path)
                    demo.status = ProDemoStatus.DOWNLOADED
                    db.commit()
                    downloaded += 1
                    continue

                try:
                    async with session.get(resource_url) as response:
                        if response.status == 200:
                            with dest_path.open("wb") as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)
                            demo.storage_path = str(dest_path)
                            demo.status = ProDemoStatus.DOWNLOADED
                            db.commit()
                            downloaded += 1
                            print(f"  Downloaded to {dest_path}")
                        else:
                            print(f"  Failed to download demo: HTTP {response.status}")
                            demo.status = ProDemoStatus.FAILED
                            db.commit()
                            failed += 1
                except Exception as exc:
                    print(f"  Error during download: {exc}")
                    demo.status = ProDemoStatus.FAILED
                    db.commit()
                    failed += 1

        print(f"Finished: downloaded={downloaded}, failed={failed}")

    finally:
        db.close()


def main() -> None:
    parser = parse_args()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    asyncio.run(download_pending_pro_demos(output_dir=output_dir, limit=args.limit))


if __name__ == "__main__":
    main()
