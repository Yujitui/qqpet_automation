from typing import Any, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User, PetData, PetInventory, UserSettings
from app.schemas.pet import PetDataResponse, PetDataUpdate, PetInfo, PetMaxInfo
from app.schemas.inventory import InventoryResponse, InventoryUpdate
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter()


def get_or_create_pet_data(db: Session, user_id: int) -> PetData:
    pet_data = db.query(PetData).filter(PetData.user_id == user_id).first()
    if not pet_data:
        pet_data = PetData(
            user_id=user_id,
            info_name="我",
            info_host="主",
            info_sex="GG",
            info_growth=0.0,
            info_hunger=3100,
            info_clean=3100,
            info_health=5,
            info_mood=1000,
            info_yb=300,
            info_intel=100,
            info_charm=215,
            info_strong=123,
            max_level=1,
            max_hunger=3100,
            max_clean=3100,
            max_mood=1000,
            max_growth_rate=260,
            max_up_growth=0,
            max_next_growth=100,
            max_stop_growth=False
        )
        db.add(pet_data)
        db.commit()
        db.refresh(pet_data)
    return pet_data


def pet_data_to_response(pet_data: PetData) -> PetDataResponse:
    return PetDataResponse(
        info=PetInfo(
            name=pet_data.info_name or "",
            host=pet_data.info_host or "",
            sex=pet_data.info_sex or "GG",
            growth=pet_data.info_growth or 0.0,
            hunger=pet_data.info_hunger or 0,
            clean=pet_data.info_clean or 0,
            health=pet_data.info_health or 5,
            mood=pet_data.info_mood or 0,
            yb=pet_data.info_yb or 0,
            intel=pet_data.info_intel or 0,
            charm=pet_data.info_charm or 0,
            strong=pet_data.info_strong or 0,
            birth_day=pet_data.info_birth_day or "",
            online_time=pet_data.info_online_time or 0.0,
            last_login_time=pet_data.info_last_login_time or 0,
            online_data_time=pet_data.info_online_data_time or 0.0
        ),
        max_info=PetMaxInfo(
            level=pet_data.max_level or 1,
            hunger=pet_data.max_hunger or 3100,
            clean=pet_data.max_clean or 3100,
            mood=pet_data.max_mood or 1000,
            growth_rate=pet_data.max_growth_rate or 260,
            up_growth=pet_data.max_up_growth or 0,
            next_growth=pet_data.max_next_growth or 100,
            stop_growth=pet_data.max_stop_growth or False
        ),
        active_option=pet_data.active_option or {},
        active_value=pet_data.active_value or {},
        other_options=pet_data.other_options or {},
        fishing=pet_data.fishing or {}
    )


@router.get("", response_model=PetDataResponse)
def get_pet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_or_create_pet_data(db, current_user.id)
    return pet_data_to_response(pet_data)


def safe_set_value(obj, attr_name, value, expected_type=None):
    if value is None:
        return
    
    if value == "" and expected_type in (int, float):
        value = 0 if expected_type == int else 0.0
    
    if expected_type == int and isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            value = 0
    elif expected_type == float and isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            value = 0.0
    
    setattr(obj, attr_name, value)


@router.patch("", response_model=PetDataResponse)
def update_pet(
    updates: PetDataUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_or_create_pet_data(db, current_user.id)
    
    update_data = updates.model_dump(exclude_unset=True)
    
    if "info" in update_data:
        info_updates = update_data["info"]
        for key, value in info_updates.items():
            field_name = f"info_{key}"
            if hasattr(pet_data, field_name):
                if key in ["growth", "online_time", "online_data_time"]:
                    safe_set_value(pet_data, field_name, value, float)
                elif key in ["hunger", "clean", "health", "mood", "yb", "intel", "charm", "strong", "last_login_time"]:
                    safe_set_value(pet_data, field_name, value, int)
                else:
                    safe_set_value(pet_data, field_name, value, str)
    
    if "max_info" in update_data:
        max_updates = update_data["max_info"]
        for key, value in max_updates.items():
            field_name = f"max_{key}"
            if hasattr(pet_data, field_name):
                if key == "stop_growth":
                    safe_set_value(pet_data, field_name, value, bool)
                else:
                    safe_set_value(pet_data, field_name, value, int)
    
    if "active_option" in update_data:
        pet_data.active_option = update_data["active_option"] or {}
    
    if "active_value" in update_data:
        pet_data.active_value = update_data["active_value"] or {}
    
    if "other_options" in update_data:
        pet_data.other_options = update_data["other_options"] or {}
    
    if "fishing" in update_data:
        pet_data.fishing = update_data["fishing"] or {}
    
    db.commit()
    db.refresh(pet_data)
    
    return pet_data_to_response(pet_data)


@router.get("/info", response_model=PetInfo)
def get_pet_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_or_create_pet_data(db, current_user.id)
    return PetInfo(
        name=pet_data.info_name or "",
        host=pet_data.info_host or "",
        sex=pet_data.info_sex or "GG",
        growth=pet_data.info_growth or 0.0,
        hunger=pet_data.info_hunger or 0,
        clean=pet_data.info_clean or 0,
        health=pet_data.info_health or 5,
        mood=pet_data.info_mood or 0,
        yb=pet_data.info_yb or 0,
        intel=pet_data.info_intel or 0,
        charm=pet_data.info_charm or 0,
        strong=pet_data.info_strong or 0,
        birth_day=pet_data.info_birth_day or "",
        online_time=pet_data.info_online_time or 0.0,
        last_login_time=pet_data.info_last_login_time or 0,
        online_data_time=pet_data.info_online_data_time or 0.0
    )


@router.patch("/info", response_model=PetInfo)
def update_pet_info(
    updates: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_or_create_pet_data(db, current_user.id)
    
    for key, value in updates.items():
        field_name = f"info_{key}"
        if hasattr(pet_data, field_name):
            if key in ["growth", "online_time", "online_data_time"]:
                safe_set_value(pet_data, field_name, value, float)
            elif key in ["hunger", "clean", "health", "mood", "yb", "intel", "charm", "strong", "last_login_time"]:
                safe_set_value(pet_data, field_name, value, int)
            else:
                safe_set_value(pet_data, field_name, value, str)
    
    db.commit()
    db.refresh(pet_data)
    
    return PetInfo(
        name=pet_data.info_name or "",
        host=pet_data.info_host or "",
        sex=pet_data.info_sex or "GG",
        growth=pet_data.info_growth or 0.0,
        hunger=pet_data.info_hunger or 0,
        clean=pet_data.info_clean or 0,
        health=pet_data.info_health or 5,
        mood=pet_data.info_mood or 0,
        yb=pet_data.info_yb or 0,
        intel=pet_data.info_intel or 0,
        charm=pet_data.info_charm or 0,
        strong=pet_data.info_strong or 0,
        birth_day=pet_data.info_birth_day or "",
        online_time=pet_data.info_online_time or 0.0,
        last_login_time=pet_data.info_last_login_time or 0,
        online_data_time=pet_data.info_online_data_time or 0.0
    )


@router.get("/active-option", response_model=Dict)
def get_active_option(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_or_create_pet_data(db, current_user.id)
    return pet_data.active_option or {}


@router.patch("/active-option", response_model=Dict)
def update_active_option(
    updates: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_or_create_pet_data(db, current_user.id)
    pet_data.active_option = updates
    db.commit()
    db.refresh(pet_data)
    return pet_data.active_option or {}
