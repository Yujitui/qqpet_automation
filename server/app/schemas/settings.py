from pydantic import BaseModel
from typing import Optional, Dict, Any


class SettingsResponse(BaseModel):
    shortcuts: dict = {}
    stop_growth: bool = False
    
    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    shortcuts: Optional[dict] = None
    stop_growth: Optional[bool] = None
