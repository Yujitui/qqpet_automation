from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class PetMarriage(Base):
    __tablename__ = "pet_marriages"

    id = Column(Integer, primary_key=True, index=True)
    pet_a_uid = Column(String(12), nullable=False, index=True)
    pet_b_uid = Column(String(12), nullable=False, index=True)
    user_a_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="active")
    intimacy = Column(Integer, default=0)

    married_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])
