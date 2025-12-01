from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...database.models import TeammateProfile as TeammateProfileDB, User
from .models import TeammateProfile, PlayerStats, TeammatePreferences
from ...ai.groq_service import GroqService
import logging


logger = logging.getLogger(__name__)


class TeammateService:
    """Service for teammate search and preference management."""

    def __init__(self) -> None:
        self.ai = GroqService()

    async def find_teammates(
        self,
        db: Session,
        current_user: User,
        preferences: TeammatePreferences,
    ) -> List[TeammateProfile]:
        """Find suitable teammates based on preferences for the current user.

        MVP implementation: uses stored TeammateProfile rows and basic filters
        by ELO range and languages/roles. Later AI-based matching can be added.
        """
        try:
            # Ensure current user has a profile (optional, can be created lazily later)
            current_profile = (
                db.query(TeammateProfileDB)
                .filter(TeammateProfileDB.user_id == current_user.id)
                .first()
            )

            query = (
                db.query(TeammateProfileDB)
                .filter(TeammateProfileDB.user_id != current_user.id)
            )

            # Filter by ELO range when data is available
            if preferences.min_elo is not None and preferences.max_elo is not None:
                query = query.filter(
                    TeammateProfileDB.elo >= preferences.min_elo,
                    TeammateProfileDB.elo <= preferences.max_elo,
                )

            candidates = query.limit(50).all()

            if not candidates and current_profile is not None:
                langs = (
                    current_profile.languages.split(",")
                    if current_profile.languages
                    else []
                )
                roles = (
                    current_profile.roles.split(",")
                    if current_profile.roles
                    else []
                )

                stats = PlayerStats(
                    faceit_elo=current_profile.elo or 0,
                    matches_played=0,
                    win_rate=0.5,
                    avg_kd=1.0,
                    avg_hs=0.5,
                    favorite_maps=(
                        current_profile.preferred_maps.split(",")
                        if current_profile.preferred_maps
                        else []
                    ),
                    last_20_matches=[],
                )

                candidate_prefs = TeammatePreferences(
                    min_elo=(current_profile.elo - 200) if current_profile.elo else 0,
                    max_elo=(current_profile.elo + 200) if current_profile.elo else 10000,
                    preferred_maps=(
                        current_profile.preferred_maps.split(",")
                        if current_profile.preferred_maps
                        else []
                    ),
                    preferred_roles=roles,
                    communication_lang=langs,
                    play_style=current_profile.play_style or "unknown",
                    time_zone="unknown",
                )

                demo_profile = TeammateProfile(
                    user_id=str(current_profile.user_id),
                    faceit_nickname=current_profile.faceit_nickname or "",
                    stats=stats,
                    preferences=candidate_prefs,
                    availability=[current_profile.availability]
                    if current_profile.availability
                    else [],
                    team_history=[],
                    about=current_profile.about,
                    discord_contact=current_profile.discord_contact,
                    telegram_contact=current_profile.telegram_contact,
                    contact_url=current_profile.contact_url,
                )

                return [demo_profile]

            if not candidates and current_profile is None:
                stats = PlayerStats(
                    faceit_elo=preferences.max_elo,
                    matches_played=0,
                    win_rate=0.5,
                    avg_kd=1.0,
                    avg_hs=0.5,
                    favorite_maps=preferences.preferred_maps,
                    last_20_matches=[],
                )

                demo_profile = TeammateProfile(
                    user_id=str(current_user.id),
                    faceit_nickname=current_user.username or current_user.email or "",
                    stats=stats,
                    preferences=preferences,
                    availability=[],
                    team_history=[],
                )

                return [demo_profile]

            result: List[TeammateProfile] = []
            for row in candidates:
                # Basic language/role matching check
                langs = (row.languages or "").split(",") if row.languages else []
                roles = (row.roles or "").split(",") if row.roles else []

                if preferences.communication_lang:
                    if not any(l in langs for l in preferences.communication_lang):
                        continue

                if preferences.preferred_roles:
                    if not any(r in roles for r in preferences.preferred_roles):
                        continue

                stats = PlayerStats(
                    faceit_elo=row.elo or 0,
                    matches_played=0,
                    win_rate=0.5,
                    avg_kd=1.0,
                    avg_hs=0.5,
                    favorite_maps=(
                        (row.preferred_maps or "").split(",")
                        if row.preferred_maps
                        else []
                    ),
                    last_20_matches=[],
                )

                candidate_prefs = TeammatePreferences(
                    min_elo=(row.elo - 200) if row.elo else 0,
                    max_elo=(row.elo + 200) if row.elo else 10000,
                    preferred_maps=(
                        (row.preferred_maps or "").split(",")
                        if row.preferred_maps
                        else []
                    ),
                    preferred_roles=roles,
                    communication_lang=langs,
                    play_style=row.play_style or "unknown",
                    time_zone="unknown",
                )

                profile = TeammateProfile(
                    user_id=str(row.user_id),
                    faceit_nickname=row.faceit_nickname or "",
                    stats=stats,
                    preferences=candidate_prefs,
                    availability=[row.availability] if row.availability else [],
                    team_history=[],
                    about=row.about,
                    discord_contact=row.discord_contact,
                    telegram_contact=row.telegram_contact,
                    contact_url=row.contact_url,
                )
                result.append(profile)

            return await self._enrich_with_ai(
                current_user=current_user,
                preferences=preferences,
                profiles=result,
                current_profile=current_profile,
            )

        except Exception as e:
            logger.exception("Failed to find teammates")
            raise HTTPException(
                status_code=500,
                detail=f"Teammate search failed: {str(e)}",
            )

    async def _enrich_with_ai(
        self,
        current_user: User,
        preferences: TeammatePreferences,
        profiles: List[TeammateProfile],
        current_profile: Optional[TeammateProfileDB] = None,
    ) -> List[TeammateProfile]:
        if not profiles:
            return profiles

        try:
            # Prefer stored Faceit-based profile data for the player when available
            player_langs = list(preferences.communication_lang or [])
            player_roles = list(preferences.preferred_roles or [])
            player_elo = preferences.max_elo
            player_style = preferences.play_style

            if current_profile is not None:
                if current_profile.elo is not None:
                    player_elo = current_profile.elo
                if current_profile.languages:
                    langs = [
                        l.strip()
                        for l in current_profile.languages.split(",")
                        if l.strip()
                    ]
                    if langs:
                        player_langs = langs
                if current_profile.roles:
                    roles = [
                        r.strip()
                        for r in current_profile.roles.split(",")
                        if r.strip()
                    ]
                    if roles:
                        player_roles = roles
                if current_profile.play_style:
                    player_style = current_profile.play_style

            player_payload = {
                "elo": player_elo,
                "preferred_roles": player_roles,
                "communication_lang": player_langs,
                "play_style": player_style,
            }

            candidates_payload = []
            for p in profiles:
                candidates_payload.append(
                    {
                        "user_id": p.user_id,
                        "faceit_nickname": p.faceit_nickname,
                        "elo": p.stats.faceit_elo,
                        "preferred_roles": p.preferences.preferred_roles,
                        "communication_lang": p.preferences.communication_lang,
                        "play_style": p.preferences.play_style,
                    }
                )

            ai_result = await self.ai.describe_teammate_matches(
                {
                    "player": player_payload,
                    "candidates": candidates_payload,
                },
                language="ru",
            )

            if isinstance(ai_result, dict):
                for p in profiles:
                    info = ai_result.get(p.user_id)
                    if not isinstance(info, dict):
                        continue
                    score = info.get("score")
                    summary = info.get("summary")
                    try:
                        if isinstance(score, (int, float)):
                            p.compatibility_score = float(score)
                    except Exception:
                        p.compatibility_score = None
                    if isinstance(summary, str):
                        p.match_summary = summary

            profiles.sort(
                key=lambda item: (item.compatibility_score or 0.0),
                reverse=True,
            )
        except Exception:
            logger.exception("Failed to enrich teammates with AI data")

        return profiles

    async def update_preferences(
        self,
        db: Session,
        current_user: User,
        preferences: TeammatePreferences,
    ) -> TeammatePreferences:
        """Update teammate search preferences for current user.

        Stores high-level preferences (roles, maps, languages, style) in
        the TeammateProfile table. ELO/level can be populated separately
        via Faceit integration.
        """
        try:
            profile = (
                db.query(TeammateProfileDB)
                .filter(TeammateProfileDB.user_id == current_user.id)
                .first()
            )

            if not profile:
                profile = TeammateProfileDB(user_id=current_user.id)
                db.add(profile)

            profile.roles = ",".join(preferences.preferred_roles or [])
            profile.languages = ",".join(preferences.communication_lang or [])
            profile.preferred_maps = ",".join(preferences.preferred_maps or [])
            profile.play_style = preferences.play_style

            if preferences.about is not None:
                profile.about = preferences.about
            if preferences.availability is not None:
                profile.availability = preferences.availability
            if preferences.discord_contact is not None:
                profile.discord_contact = preferences.discord_contact
            if preferences.telegram_contact is not None:
                profile.telegram_contact = preferences.telegram_contact
            if preferences.contact_url is not None:
                profile.contact_url = preferences.contact_url

            db.commit()
            db.refresh(profile)

            return preferences
        except Exception as e:
            logger.exception("Failed to update preferences")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update preferences: {str(e)}",
            )
