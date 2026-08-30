from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.datetime import utcnow
import uuid

class Vital(Base):
    __tablename__ = "vitals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    heart_rate = Column(Float, nullable=True)
    systolic_bp = Column(Float, nullable=True)
    diastolic_bp = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    respiratory_rate = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    patient = relationship("Patient", back_populates="vitals")
