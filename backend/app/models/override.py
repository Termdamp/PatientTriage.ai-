from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.enums import Priority
from app.utils.datetime import utcnow
import uuid

class Override(Base):
    __tablename__ = "overrides"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    assessment_id = Column(String, nullable=False)
    original_priority = Column(SAEnum(Priority), nullable=False)
    new_priority = Column(SAEnum(Priority), nullable=False)
    reason = Column(String, nullable=False)
    clinician_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    patient = relationship("Patient", back_populates="overrides")

