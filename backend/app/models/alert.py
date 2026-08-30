from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.enums import AlertType, AlertSeverity
from app.utils.datetime import utcnow
import uuid

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)
    type = Column(SAEnum(AlertType), nullable=False)
    severity = Column(SAEnum(AlertSeverity), nullable=False)
    message = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    acknowledged = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="alerts")

