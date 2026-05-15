from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.api.deps import get_db, get_current_user
from app.models import User, Friend, PetData
from app.schemas.friend import FriendCreate, FriendResponse, FriendAction
from app.ws.manager import manager

router = APIRouter()


def _user_to_friend_response(friend_record: Friend, user: User, db: Session) -> FriendResponse:
    pet = db.query(PetData).filter(PetData.user_id == user.id).first()
    return FriendResponse(
        friend_id=friend_record.id,
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        is_online=False,
        pet_public_uid=pet.public_uid if pet else None,
        pet_name=pet.info_name if pet else "",
        status=friend_record.status,
        created_at=friend_record.created_at or datetime.utcnow(),
    )


@router.get("/friends", response_model=List[FriendResponse])
def list_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friends = db.query(Friend).filter(
        or_(
            and_(Friend.user_id == current_user.id, Friend.status == "accepted"),
            and_(Friend.friend_user_id == current_user.id, Friend.status == "accepted"),
        )
    ).all()

    results = []
    for f in friends:
        if f.user_id == current_user.id:
            friend_user = f.friend
        else:
            friend_user = f.user
        results.append(_user_to_friend_response(f, friend_user, db))
    return results


@router.get("/friends/pending", response_model=List[FriendResponse])
def list_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pending_received = db.query(Friend).filter(
        Friend.friend_user_id == current_user.id,
        Friend.status == "pending",
    ).all()

    results = []
    for f in pending_received:
        results.append(_user_to_friend_response(f, f.user, db))
    return results


@router.post("/friends/add", response_model=FriendResponse)
def add_friend(
    request: FriendCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    nickname = request.nickname.strip()
    if not nickname:
        raise HTTPException(status_code=400, detail="昵称不能为空")

    target = db.query(User).filter(User.nickname == nickname).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    existing = db.query(Friend).filter(
        or_(
            and_(Friend.user_id == current_user.id, Friend.friend_user_id == target.id),
            and_(Friend.user_id == target.id, Friend.friend_user_id == current_user.id),
        )
    ).first()

    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=409, detail="已经是好友")
        if existing.status == "pending":
            raise HTTPException(status_code=409, detail="已发送过好友请求")
        if existing.status == "blocked":
            raise HTTPException(status_code=403, detail="无法添加该用户")

    friend = Friend(user_id=current_user.id, friend_user_id=target.id, status="pending")
    db.add(friend)
    db.commit()
    db.refresh(friend)

    return _user_to_friend_response(friend, target, db)


@router.post("/friends/{friend_id}/respond")
def respond_friend_request(
    friend_id: int,
    action: FriendAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friend_rel = db.query(Friend).filter(
        Friend.id == friend_id,
        Friend.friend_user_id == current_user.id,
        Friend.status == "pending",
    ).first()

    if not friend_rel:
        raise HTTPException(status_code=404, detail="好友请求不存在")

    if action.action == "accept":
        friend_rel.status = "accepted"
        friend_rel.updated_at = datetime.utcnow()
        db.commit()
        return _user_to_friend_response(friend_rel, friend_rel.user, db)
    elif action.action == "reject":
        db.delete(friend_rel)
        db.commit()
        return {"message": "已拒绝好友请求"}
    elif action.action == "block":
        friend_rel.status = "blocked"
        friend_rel.updated_at = datetime.utcnow()
        db.commit()
        return _user_to_friend_response(friend_rel, friend_rel.user, db)
    else:
        raise HTTPException(status_code=400, detail="无效操作")


@router.delete("/friends/{friend_id}")
def remove_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friend_rel = db.query(Friend).filter(
        Friend.id == friend_id,
        or_(
            Friend.user_id == current_user.id,
            Friend.friend_user_id == current_user.id,
        ),
        Friend.status == "accepted",
    ).first()

    if not friend_rel:
        raise HTTPException(status_code=404, detail="好友关系不存在")

    db.delete(friend_rel)
    db.commit()

    return {"message": "已删除好友"}
