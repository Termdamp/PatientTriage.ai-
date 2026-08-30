from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.enums import Priority, RecommendedAction
from app.utils.datetime import utcnow
import uuid

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    priority = Column(SAEnum(Priority), nullable=False)
    confidence = Column(Float, nullable=False)
    safety_floor = Column(SAEnum(Priority), nullable=True)
    reasons = Column(JSON, nullable=False, default=list)
    recommended_action = Column(SAEnum(RecommendedAction), nullable=False)
    model_version = Column(String, nullable=False, default="prototype-rules-v1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    deteriorating = Column(Integer, nullable=False, default=0)
    deterioration_severity = Column(String, nullable=True)
    safety_flags = Column(JSON, nullable=False, default=list)
    age_group = Column(String, nullable=True)
    data_quality = Column(Float, nullable=True)
    explanation = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="assessments")
