from pydantic import BaseModel
from typing import Optional, List


class InventoryItems(BaseModel):
    food: List[str] = []
    commodity: List[str] = []
    medicine: List[str] = []
    background: List[str] = []


class InventoryResponse(InventoryItems):
    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    food: Optional[List[str]] = None
    commodity: Optional[List[str]] = None
    medicine: Optional[List[str]] = None
    background: Optional[List[str]] = None
