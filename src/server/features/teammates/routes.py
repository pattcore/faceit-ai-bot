from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...auth.dependencies import get_current_active_user
from ...database.models import User
from ...database.connection import get_db
from ..teammates.service import TeammateService
from ..teammates.models import TeammateProfile, TeammatePreferences
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teammates", tags=["teammates"])

teammate_service = TeammateService()


@router.post("/search", response_model=List[TeammateProfile])
async def search_teammates(
    preferences: TeammatePreferences,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Search teammates based on preferences for the current user."""
    return await teammate_service.find_teammates(
        db=db,
        current_user=current_user,
        preferences=preferences,
    )


@router.put("/preferences", response_model=TeammatePreferences)
async def update_preferences(
    preferences: TeammatePreferences,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update teammate search preferences for the current user."""
    return await teammate_service.update_preferences(
        db=db,
        current_user=current_user,
        preferences=preferences,
    )
