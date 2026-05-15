from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FriendCreate(BaseModel):
    nickname: str


class FriendResponse(BaseModel):
    friend_id: int
    user_id: int
    username: str
    nickname: str
    is_online: bool = False
    pet_public_uid: Optional[str] = None
    pet_name: str = ""
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FriendAction(BaseModel):
    action: str  # accept / reject / block
