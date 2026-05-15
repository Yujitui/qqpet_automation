from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class PetData(Base):
    __tablename__ = "pet_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    info_name = Column(String(50), default="")
    info_host = Column(String(50), default="")
    info_sex = Column(String(2), default="GG")
    info_growth = Column(Float, default=0.0)
    info_hunger = Column(Integer, default=3100)
    info_clean = Column(Integer, default=3100)
    info_health = Column(Integer, default=5)
    info_mood = Column(Integer, default=1000)
    info_yb = Column(Integer, default=300)
    info_intel = Column(Integer, default=100)
    info_charm = Column(Integer, default=215)
    info_strong = Column(Integer, default=123)
    info_birth_day = Column(String(20), default="")
    info_online_time = Column(Float, default=0.0)
    info_last_login_time = Column(BigInteger, default=0)
    info_online_data_time = Column(Float, default=0.0)
    
    max_level = Column(Integer, default=1)
    max_hunger = Column(Integer, default=3100)
    max_clean = Column(Integer, default=3100)
    max_mood = Column(Integer, default=1000)
    max_growth_rate = Column(Integer, default=260)
    max_up_growth = Column(Integer, default=0)
    max_next_growth = Column(Integer, default=100)
    max_stop_growth = Column(Boolean, default=False)
    
    public_uid = Column(String(12), unique=True, nullable=False, index=True)
    marriage_status = Column(String(20), default="single")
    spouse_uid = Column(String(12), nullable=True)
    intimacy = Column(Integer, default=0)

    active_option = Column(JSON, default={})
    active_value = Column(JSON, default={})
    other_options = Column(JSON, default={})
    fishing = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="pet_data")
