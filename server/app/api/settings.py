from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User, UserSettings
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter()


def get_or_create_settings(db: Session, user_id: int) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(
            user_id=user_id,
            shortcuts={},
            stop_growth=False
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=SettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    settings = get_or_create_settings(db, current_user.id)
    return SettingsResponse(
        shortcuts=settings.shortcuts or {},
        stop_growth=settings.stop_growth or False
    )


@router.patch("", response_model=SettingsResponse)
def update_settings(
    updates: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    settings = get_or_create_settings(db, current_user.id)
    update_data = updates.model_dump(exclude_unset=True)
    
    if "shortcuts" in update_data and update_data["shortcuts"] is not None:
        settings.shortcuts = update_data["shortcuts"]
    
    if "stop_growth" in update_data and update_data["stop_growth"] is not None:
        settings.stop_growth = update_data["stop_growth"]
    
    db.commit()
    db.refresh(settings)
    
    return SettingsResponse(
        shortcuts=settings.shortcuts or {},
        stop_growth=settings.stop_growth or False
    )
