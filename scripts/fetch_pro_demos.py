from __future__ import annotations

import asyncio
import json
from argparse import ArgumentParser
from pathlib import Path

from src.server.database.connection import SessionLocal
from src.server.database.models import ProDemo, ProDemoStatus
from src.server.integrations.faceit_client import FaceitAPIClient


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(
        description="Fetch professional CS2 demos from Faceit for configured players.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/pro_players.json",
        help="Path to JSON file with Faceit players list.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of recent matches per player to fetch.",
    )
    return parser


async def fetch_pro_demos(config_path: Path, limit: int) -> None:
    if not config_path.is_file():
        raise SystemExit(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        players = json.load(f)

    if not isinstance(players, list):
        raise SystemExit("Config JSON must be a list of player objects")

    client = FaceitAPIClient()
    db = SessionLocal()
    created = 0

    try:
        for entry in players:
            if not isinstance(entry, dict):
                continue

            nickname = entry.get("nickname")
            player_id = entry.get("faceit_id")

            if not nickname and not player_id:
                continue

            label = nickname or player_id
            print(f"Fetching matches for {label}...")

            if not player_id and nickname:
                try:
                    player_data = await client.get_player_by_nickname(nickname)
                except Exception as exc:
                    print(f"Failed to get player by nickname {nickname}: {exc}")
                    continue

                if not player_data:
                    continue

                player_id = player_data.get("player_id")

            if not player_id:
                continue

            try:
                history = await client.get_match_history(player_id=player_id, limit=limit)
            except Exception as exc:
                print(f"Failed to get match history for {player_id}: {exc}")
                continue

            for item in history or []:
                if not isinstance(item, dict):
                    continue

                match_id = item.get("match_id")
                if not match_id:
                    continue

                exists = (
                    db.query(ProDemo)
                    .filter(ProDemo.faceit_match_id == match_id)
                    .first()
                )
                if exists:
                    continue

                pro_demo = ProDemo(
                    faceit_match_id=match_id,
                    faceit_player_id=player_id,
                    faceit_nickname=nickname,
                    status=ProDemoStatus.QUEUED,
                )
                db.add(pro_demo)
                created += 1

            db.commit()

    finally:
        db.close()

    print(f"Created {created} pro demo records")


def main() -> None:
    parser = parse_args()
    args = parser.parse_args()

    config_path = Path(args.config)
    asyncio.run(fetch_pro_demos(config_path=config_path, limit=args.limit))


if __name__ == "__main__":
    main()
