from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.audit_service import get_audit_events

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("")
def get_all_audit_events(limit: int = 100, db: Session = Depends(get_db)):
    events = get_audit_events(db, limit=limit)
    return {
        "events": [{
            "id": e.id, "patientId": e.patient_id, "eventType": e.event_type,
            "actor": e.actor, "description": e.description,
            "metadata": e.metadata_, "createdAt": e.created_at
        } for e in events],
        "totalCount": len(events)
    }
