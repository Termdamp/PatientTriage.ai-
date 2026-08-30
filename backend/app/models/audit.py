from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.datetime import utcnow
import uuid

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)
    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=False, default="SYSTEM")
    description = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    patient = relationship("Patient", back_populates="audit_events")

