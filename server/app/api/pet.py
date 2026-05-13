import random
from datetime import datetime
from typing import Any, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User, PetData, PetInventory
from app.schemas.pet import PetDataResponse, PetDataUpdate, PetInfo, PetMaxInfo

router = APIRouter()


def get_pet_data(db: Session, user_id: int) -> PetData:
    pet_data = db.query(PetData).filter(PetData.user_id == user_id).first()
    if not pet_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="宠物数据不存在，请先初始化")
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


@router.post("/init", response_model=PetDataResponse)
def init_pet(
    reset: bool = Query(False),
    sex: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = db.query(PetData).filter(PetData.user_id == current_user.id).first()

    if pet_data and not reset:
        return pet_data_to_response(pet_data)

    if pet_data and reset:
        db.query(PetInventory).filter(PetInventory.user_id == current_user.id).delete()
        db.query(PetData).filter(PetData.user_id == current_user.id).delete()

    if sex in ("GG", "MM"):
        pet_sex = sex
    else:
        pet_sex = random.choice(["GG", "MM"])

    while True:
        _intel = random.randint(1, 10)
        _charm = random.randint(1, 10)
        _strong = 20 - _intel - _charm
        if 1 <= _strong <= 10:
            break

    STARTER_FOOD = [
        ("102010001", 5),
        ("102010011", 10),
        ("102010012", 10),
        ("102010002", 20),
    ]
    STARTER_COMMODITY = [
        ("102020001", 10),
        ("102020012", 15),
        ("102020003", 20),
        ("102020010", 20),
    ]

    items_value = 0
    inventory_items = {"food": [], "commodity": [], "medicine": [], "background": []}

    for _ in range(random.randint(1, 2)):
        item_id, price = random.choice(STARTER_FOOD)
        qty = random.randint(1, 2)
        inventory_items["food"].append(f"_{item_id}-{qty}")
        items_value += price * qty

    for _ in range(random.randint(1, 2)):
        item_id, price = random.choice(STARTER_COMMODITY)
        qty = random.randint(1, 2)
        inventory_items["commodity"].append(f"_{item_id}-{qty}")
        items_value += price * qty

    _yb = max(300 - items_value, 0)

    now = datetime.utcnow()
    pet_data = PetData(
        user_id=current_user.id,
        info_name="宝宝",
        info_host="主人",
        info_sex=pet_sex,
        info_growth=0.0,
        info_hunger=3100,
        info_clean=3100,
        info_health=5,
        info_mood=1000,
        info_yb=_yb,
        info_intel=_intel,
        info_charm=_charm,
        info_strong=_strong,
        info_birth_day=now.strftime("%Y-%m-%d %H"),
        max_level=1,
        max_hunger=3100,
        max_clean=3100,
        max_mood=1000,
        max_growth_rate=260,
        max_up_growth=0,
        max_next_growth=100,
        max_stop_growth=False,
        active_value={
            "work": {},
            "study": {"chinese": 0, "mathematics": 0, "politics": 0,
                       "music": 0, "art": 0, "manner": 0,
                       "pe": 0, "labouring": 0, "wushu": 0}
        },
        fishing={"fishes": [], "harvestfish": 0, "allvipcnt": 0,
                  "canusecnt": 0, "power": 30, "needTime": 1}
    )
    db.add(pet_data)

    inventory = PetInventory(
        user_id=current_user.id,
        items=inventory_items
    )
    db.add(inventory)
    db.commit()
    db.refresh(pet_data)

    return pet_data_to_response(pet_data)


@router.get("", response_model=PetDataResponse)
def get_pet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_pet_data(db, current_user.id)
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
    pet_data = get_pet_data(db, current_user.id)

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
    pet_data = get_pet_data(db, current_user.id)
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
    pet_data = get_pet_data(db, current_user.id)

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
    pet_data = get_pet_data(db, current_user.id)
    return pet_data.active_option or {}


@router.patch("/active-option", response_model=Dict)
def update_active_option(
    updates: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    pet_data = get_pet_data(db, current_user.id)
    pet_data.active_option = updates
    db.commit()
    db.refresh(pet_data)
    return pet_data.active_option or {}
