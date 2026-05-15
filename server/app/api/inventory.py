from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User, PetInventory
from app.schemas.inventory import InventoryResponse, InventoryUpdate

router = APIRouter()


def get_inventory(db: Session, user_id: int) -> PetInventory:
    inventory = db.query(PetInventory).filter(PetInventory.user_id == user_id).first()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="背包数据不存在")
    return inventory


@router.get("", response_model=InventoryResponse)
def get_user_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    inventory = get_inventory(db, current_user.id)
    items = inventory.items or {}
    return InventoryResponse(
        food=items.get("food", []),
        commodity=items.get("commodity", []),
        medicine=items.get("medicine", []),
        background=items.get("background", [])
    )


@router.patch("", response_model=InventoryResponse)
def update_inventory(
    updates: InventoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    inventory = get_inventory(db, current_user.id)
    update_data = updates.model_dump(exclude_unset=True)

    items = dict(inventory.items or {})

    for key, value in update_data.items():
        if value is not None:
            items[key] = value

    inventory.items = items
    db.commit()
    db.refresh(inventory)

    return InventoryResponse(
        food=items.get("food", []),
        commodity=items.get("commodity", []),
        medicine=items.get("medicine", []),
        background=items.get("background", [])
    )


@router.post("/use", response_model=InventoryResponse)
def use_item(
    item_type: str,
    item_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    inventory = get_inventory(db, current_user.id)
    items = inventory.items or {}

    if item_type not in items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的物品类型: {item_type}"
        )

    item_list = items[item_type]
    found = False

    for i, item_str in enumerate(item_list):
        parts = item_str.split("-")
        if len(parts) == 2 and parts[0] == item_key:
            count = int(parts[1])
            if count > 1:
                item_list[i] = f"{item_key}-{count - 1}"
            else:
                item_list.pop(i)
            found = True
            break

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物品 {item_key} 不存在于 {item_type} 中"
        )

    items[item_type] = item_list
    inventory.items = items
    db.commit()
    db.refresh(inventory)

    return InventoryResponse(
        food=items.get("food", []),
        commodity=items.get("commodity", []),
        medicine=items.get("medicine", []),
        background=items.get("background", [])
    )
