from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...database.models import TeammateProfile as TeammateProfileDB, User
from .models import TeammateProfile, PlayerStats, TeammatePreferences
import logging


logger = logging.getLogger(__name__)


class TeammateService:
    """Service for teammate search and preference management."""

    async def find_teammates(
        self,
        db: Session,
        current_user: User,
        preferences: TeammatePreferences,
    ) -> List[TeammateProfile]:
        """Find suitable teammates based on preferences for the current user.

        MVP implementation: uses stored TeammateProfile rows and basic filters
        by ELO range and languages/roles. Later можно будет добавить AI-совместимость.
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
                )
                result.append(profile)

            return result

        except Exception as e:
            logger.exception("Failed to find teammates")
            raise HTTPException(
                status_code=500,
                detail=f"Teammate search failed: {str(e)}",
            )

    async def update_preferences(
        self,
        db: Session,
        current_user: User,
        preferences: TeammatePreferences,
    ) -> TeammatePreferences:
        """Update teammate search preferences for current user.

        Stores high-level preferences (roles, maps, languages, style) in
        TeammateProfile table. ELO/level можно будет заполнить отдельно
        через Faceit-интеграцию.
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
