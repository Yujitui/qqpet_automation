from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import bcrypt
from jose import jwt

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def create_access_token(
    subject: Any, 
    expires_delta: Optional[timedelta] = None
) -> tuple[str, str]:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = str(uuid4())
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "jti": jti,
        "type": "access"
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt, jti


def create_refresh_token(
    subject: Any,
    expires_delta: Optional[timedelta] = None
) -> tuple[str, str]:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    jti = str(uuid4())
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "jti": jti,
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt, jti


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None
