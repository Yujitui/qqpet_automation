from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class PetInfo(BaseModel):
    name: str = ""
    host: str = ""
    sex: str = "GG"
    growth: float = 0.0
    hunger: int = 3100
    clean: int = 3100
    health: int = 5
    mood: int = 1000
    yb: int = 300
    intel: int = 100
    charm: int = 215
    strong: int = 123
    birth_day: str = ""
    online_time: float = 0.0
    last_login_time: int = 0
    online_data_time: float = 0.0


class PetMaxInfo(BaseModel):
    level: int = 1
    hunger: int = 3100
    clean: int = 3100
    mood: int = 1000
    growth_rate: int = 260
    up_growth: int = 0
    next_growth: int = 100
    stop_growth: bool = False


class PetDataResponse(BaseModel):
    info: PetInfo
    max_info: PetMaxInfo
    public_uid: str = ""
    marriage_status: str = "single"
    spouse_uid: Optional[str] = None
    intimacy: int = 0
    active_option: dict = {}
    active_value: dict = {}
    other_options: dict = {}
    fishing: dict = {}
    
    class Config:
        from_attributes = True


class PetDataUpdate(BaseModel):
    info: Optional[dict] = None
    max_info: Optional[dict] = None
    active_option: Optional[dict] = None
    active_value: Optional[dict] = None
    other_options: Optional[dict] = None
    fishing: Optional[dict] = None
