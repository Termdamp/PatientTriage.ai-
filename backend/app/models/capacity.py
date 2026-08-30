from sqlalchemy import Column, String, Integer, DateTime, Float
from app.core.database import Base
from app.utils.datetime import utcnow
import uuid

class Capacity(Base):
    __tablename__ = "capacity"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    total_beds = Column(Integer, nullable=False, default=50)
    occupied_beds = Column(Integer, nullable=False, default=0)
    critical_beds = Column(Integer, nullable=False, default=10)
    critical_occupied = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
