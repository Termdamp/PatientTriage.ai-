from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Bed(Base):
    __tablename__ = "beds"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False, default="GENERAL")  # GENERAL, CRITICAL_CARE
    status = Column(String, nullable=False, default="AVAILABLE")  # AVAILABLE, OCCUPIED, MAINTENANCE
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)

    patient = relationship("Patient", back_populates="bed")
