from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.queue_service import get_queue
from app.schemas.queue import QueueResponse, QueueItem
from app.utils.datetime import utcnow

router = APIRouter(prefix="/queue", tags=["queue"])

@router.get("")
def get_patient_queue(db: Session = Depends(get_db)):
    entries = get_queue(db)
    items = []
    for idx, entry in enumerate(entries):
        items.append({
            "id": entry.patient_id,
            "name": entry.name,
            "age": entry.age,
            "gender": entry.gender,
            "chiefComplaint": entry.chief_complaint,
            "priority": entry.effective_priority.value,
            "riskScore": entry.risk_score,
            "confidence": entry.confidence,
            "waitMinutes": round(entry.wait_minutes, 1),
            "deteriorating": entry.deteriorating,
            "safetyFlags": entry.safety_flags,
            "reasons": entry.reasons,
            "recommendedAction": entry.recommended_action,
            "queuePosition": idx + 1,
            "overrideApplied": entry.override_priority is not None
        })
    from app.utils.enums import Priority
    counts = {p: sum(1 for e in entries if e.effective_priority == p) for p in Priority}
    return {
        "patients": items,
        "totalCount": len(items),
        "criticalCount": counts[Priority.CRITICAL],
        "highCount": counts[Priority.HIGH],
        "moderateCount": counts[Priority.MODERATE],
        "lowCount": counts[Priority.LOW],
        "updatedAt": utcnow()
    }
