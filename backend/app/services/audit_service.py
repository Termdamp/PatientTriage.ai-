import logging
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent
from app.utils.enums import EventType
from app.utils.datetime import utcnow
import uuid
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def create_audit_event(
    db: Session,
    event_type: str,
    description: str,
    patient_id: Optional[str] = None,
    actor: str = "SYSTEM",
    metadata: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    event = AuditEvent(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        event_type=event_type,
        actor=actor,
        description=description,
        metadata_=metadata or {},
        created_at=utcnow()
    )
    db.add(event)
    db.flush()  # Get ID without committing
    logger.debug(f"Audit event created: {event_type} for patient {patient_id}")
    return event

def get_audit_events(db: Session, patient_id: Optional[str] = None, limit: int = 100):
    query = db.query(AuditEvent)
    if patient_id:
        query = query.filter(AuditEvent.patient_id == patient_id)
    return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()
