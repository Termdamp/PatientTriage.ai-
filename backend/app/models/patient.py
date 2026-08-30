from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.enums import PatientStatus
from app.utils.datetime import utcnow
from app.utils.ids import patient_id

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=patient_id)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    chief_complaint = Column(String, nullable=False)
    symptoms = Column(JSON, nullable=False, default=list)  # List[str]
    medical_history = Column(JSON, nullable=True, default=list)  # List[str]
    history_available = Column(Boolean, nullable=False, default=True)
    arrival_time = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    status = Column(SAEnum(PatientStatus), nullable=False, default=PatientStatus.WAITING)
    next_reassessment_due = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    vitals = relationship("Vital", back_populates="patient", order_by="Vital.timestamp")
    assessments = relationship("Assessment", back_populates="patient", order_by="Assessment.created_at")
    alerts = relationship("Alert", back_populates="patient", order_by="Alert.created_at")
    overrides = relationship("Override", back_populates="patient", order_by="Override.created_at")
    audit_events = relationship("AuditEvent", back_populates="patient", order_by="AuditEvent.created_at")
    bed = relationship("Bed", back_populates="patient", uselist=False)
