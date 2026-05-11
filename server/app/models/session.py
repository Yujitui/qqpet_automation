from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    token_jti = Column(String(100), unique=True, nullable=False, index=True)
    device_info = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")
