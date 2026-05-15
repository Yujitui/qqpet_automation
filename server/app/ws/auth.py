from typing import Optional
from fastapi import WebSocket, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import SessionLocal
from app.models import Session as SessionModel, User


class WSAuthResult:
    def __init__(self, success: bool, user_id: Optional[int] = None, user: Optional[User] = None, error: Optional[str] = None):
        self.success = success
        self.user_id = user_id
        self.user = user
        self.error = error


async def verify_ws_token(ws: WebSocket) -> WSAuthResult:
    token = ws.query_params.get("token")
    if not token:
        return WSAuthResult(False, error="缺少 token 参数")

    payload = decode_token(token)
    if payload is None:
        return WSAuthResult(False, error="token 无效或已过期")

    token_type = payload.get("type")
    if token_type != "access":
        return WSAuthResult(False, error="请使用 access token")

    jti = payload.get("jti")
    db: Session = SessionLocal()
    try:
        session = db.query(SessionModel).filter(
            SessionModel.token_jti == jti,
            SessionModel.is_active == True
        ).first()

        if not session:
            return WSAuthResult(False, error="会话已过期或已失效")

        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return WSAuthResult(False, error="用户不存在")

        if not user.is_active:
            return WSAuthResult(False, error="用户已被禁用")

        return WSAuthResult(True, user_id=user_id, user=user)
    finally:
        db.close()
