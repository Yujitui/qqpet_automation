from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class PetInventory(Base):
    __tablename__ = "pet_inventory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    items = Column(
        JSON, 
        default={
            "food": [], 
            "commodity": [], 
            "medicine": [], 
            "background": []
        }
    )
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="inventory")
