from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
from demoparser2 import DemoParser


def extract_player_feature_rows(demo_path: Path) -> List[Dict]:
    """Extract basic per-player features from a CS2 demo file.

    Returns a list of dicts that can be directly used to populate DemoFeature
    rows (except for DB-specific fields like pro_demo_id and source).
    """
    if not demo_path.is_file():
        raise FileNotFoundError(f"Demo file not found: {demo_path}")

    parser = DemoParser(demopath=str(demo_path))

    header = parser.parse_header()
    rounds_df = parser.parse_rounds()
    kills_df = parser.parse_kills()
    damage_df = parser.parse_damage()

    if not isinstance(kills_df, pd.DataFrame):
        kills_df = pd.DataFrame(kills_df)
    if not isinstance(damage_df, pd.DataFrame):
        damage_df = pd.DataFrame(damage_df)

    total_rounds = 0
    try:
        total_rounds = int(len(rounds_df)) if hasattr(rounds_df, "__len__") else 0
    except Exception:
        total_rounds = 0

    if total_rounds <= 0:
        duration = int(header.get("duration", 0) or 0)
        total_rounds = max(1, duration // 75)  # ~75s per round heuristic

    players = set()

    if not kills_df.empty:
        if "attackername" in kills_df.columns:
            players.update(kills_df["attackername"].dropna().unique())
        if "victimname" in kills_df.columns:
            players.update(kills_df["victimname"].dropna().unique())

    if not damage_df.empty and "attackername" in damage_df.columns:
        players.update(damage_df["attackername"].dropna().unique())

    rows: List[Dict] = []

    for name in players:
        if not name:
            continue

        kills = 0
        deaths = 0
        headshots = 0
        total_damage = 0.0

        if not kills_df.empty:
            if "attackername" in kills_df.columns:
                attacker_mask = kills_df["attackername"] == name
                kills = int(attacker_mask.sum())

                if "headshot" in kills_df.columns:
                    headshots = int(
                        kills_df.loc[attacker_mask & (kills_df["headshot"] == True)].shape[0]  # noqa: E712
                    )

            if "victimname" in kills_df.columns:
                deaths = int((kills_df["victimname"] == name).sum())

        if not damage_df.empty and {
            "attackername",
            "hp_damage",
        }.issubset(set(damage_df.columns)):
            player_damage = damage_df[damage_df["attackername"] == name]
            total_damage = float(player_damage["hp_damage"].sum()) if not player_damage.empty else 0.0

        adr = total_damage / float(total_rounds) if total_rounds > 0 else 0.0
        headshot_pct = (headshots / kills * 100.0) if kills > 0 else None

        # Simple impact proxy: more kills and damage -> higher impact.
        round_impact_score = float(kills) + 0.003 * float(total_damage)

        rows.append(
            {
                "steam_id": str(name),
                "round_number": None,
                "kills": kills,
                "deaths": deaths,
                "assists": None,
                "damage": total_damage,
                "adr": adr,
                "kast": None,
                "rating_2_0": None,
                "opening_duels_won": None,
                "multikills": None,
                "clutches_won": None,
                "trade_kills": None,
                "avg_distance_to_teammates": None,
                "avg_distance_to_bombsite": None,
                "time_in_aggressive_positions": None,
                "time_in_passive_positions": None,
                "early_round_pushes": None,
                "late_round_rotations": None,
                "save_rounds": None,
                "suicidal_peeks": None,
                "nades_thrown": None,
                "flashes_thrown": None,
                "flash_assists": None,
                "smokes_thrown": None,
                "smokes_blocking_time": None,
                "molotovs_thrown": None,
                "molotovs_area_denial_time": None,
                "avg_money_spent": None,
                "eco_rounds_played": None,
                "force_buy_rounds": None,
                "full_buy_rounds": None,
                "weapon_tier_score": None,
                "round_impact_score": round_impact_score,
                "clutch_impact": None,
                "entry_impact": None,
            }
        )

    return rows
