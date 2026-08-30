from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base
from app.utils.datetime import utcnow
import uuid

class ResourceConfiguration(Base):
    __tablename__ = "resource_configurations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doctors_total = Column(Integer, nullable=False, default=5)
    doctors_active = Column(Integer, nullable=False, default=3)
    nurses_total = Column(Integer, nullable=False, default=12)
    nurses_active = Column(Integer, nullable=False, default=8)
    ventilators_total = Column(Integer, nullable=False, default=4)
    ventilators_active = Column(Integer, nullable=False, default=1)
    monitors_total = Column(Integer, nullable=False, default=8)
    monitors_active = Column(Integer, nullable=False, default=2)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
