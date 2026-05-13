from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_token_payload
from app.config import settings
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_token
)
from app.models import User, Session as SessionModel, PetData, PetInventory
from app.schemas.auth import (
    UserLogin, 
    UserCreate,
    Token, 
    UserResponse,
    Message
)

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
def register(
    form_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    existing = db.query(User).filter(User.username == form_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    hashed_password = get_password_hash(form_data.password)
    user = User(
        username=form_data.username,
        email=form_data.email,
        hashed_password=hashed_password,
        is_active=False,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/login")
def login(
    form_data: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        hashed_password = get_password_hash(form_data.password)
        user = User(
            username=form_data.username,
            hashed_password=hashed_password,
            is_active=False,
            is_admin=False
        )
        db.add(user)
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"status": "created", "message": "账号已注册，请联系管理员激活"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号未激活，请联系管理员",
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db.query(SessionModel).filter(
        SessionModel.user_id == user.id,
        SessionModel.is_active == True
    ).update({"is_active": False})
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token, access_jti = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token, refresh_jti = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    
    now = datetime.utcnow()
    access_session = SessionModel(
        user_id=user.id,
        token_jti=access_jti,
        is_active=True,
        expires_at=now + access_token_expires
    )
    refresh_session = SessionModel(
        user_id=user.id,
        token_jti=refresh_jti,
        is_active=True,
        expires_at=now + refresh_token_expires
    )
    db.add(access_session)
    db.add(refresh_session)
    
    user.last_login_at = now
    db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", response_model=Message)
def logout(
    current_user: User = Depends(get_current_user),
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db)
) -> Any:
    jti = payload.get("jti")
    db.query(SessionModel).filter(
        SessionModel.token_jti == jti
    ).update({"is_active": False})
    db.commit()
    
    return Message(message="已登出")


@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=Token)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Any:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 refresh token"
        )
    
    jti = payload.get("jti")
    session = db.query(SessionModel).filter(
        SessionModel.token_jti == jti,
        SessionModel.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效"
        )
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    session.is_active = False
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token, access_jti = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token, refresh_jti = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    
    now = datetime.utcnow()
    access_session = SessionModel(
        user_id=user.id,
        token_jti=access_jti,
        is_active=True,
        expires_at=now + access_token_expires
    )
    refresh_session = SessionModel(
        user_id=user.id,
        token_jti=refresh_jti,
        is_active=True,
        expires_at=now + refresh_token_expires
    )
    db.add(access_session)
    db.add(refresh_session)
    db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )
