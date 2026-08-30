from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.core.database import get_db
from app.schemas.override import OverrideRequest, OverrideResponse
from app.services.patient_service import get_patient, get_latest_assessment
from app.services.audit_service import create_audit_event
from app.models.override import Override
from app.realtime.websocket_manager import manager
from app.realtime.events import WebSocketEvent
from app.utils.enums import EventType
from app.utils.datetime import utcnow
import logging

router = APIRouter(prefix="/override", tags=["override"])
logger = logging.getLogger(__name__)

@router.post("")
async def override_priority(request: OverrideRequest, db: Session = Depends(get_db)):
    patient = get_patient(db, request.patientId)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {request.patientId} not found")

    assessment = get_latest_assessment(db, request.patientId)
    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found for patient")

    override = Override(
        id=str(uuid.uuid4()),
        patient_id=request.patientId,
        assessment_id=request.assessmentId,
        original_priority=assessment.priority,
        new_priority=request.newPriority,
        reason=request.reason,
        clinician_id=request.clinicianId,
        created_at=utcnow()
    )
    db.add(override)

    create_audit_event(
        db, EventType.CLINICIAN_OVERRIDE,
        f"Clinician {request.clinicianId} overrode priority: {assessment.priority.value} → {request.newPriority.value}. Reason: {request.reason}",
        patient_id=request.patientId,
        actor=request.clinicianId,
        metadata={
            "originalPriority": assessment.priority.value,
            "newPriority": request.newPriority.value,
            "assessmentId": request.assessmentId,
        }
    )
    db.commit()

    await manager.broadcast(WebSocketEvent.OVERRIDE_APPLIED, {
        "patientId": request.patientId,
        "originalPriority": assessment.priority.value,
        "newPriority": request.newPriority.value,
        "clinicianId": request.clinicianId
    })
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "override_applied"})

    return {
        "id": override.id,
        "patientId": override.patient_id,
        "assessmentId": override.assessment_id,
        "originalPriority": override.original_priority.value,
        "newPriority": override.new_priority.value,
        "reason": override.reason,
        "clinicianId": override.clinician_id,
        "createdAt": override.created_at
    }
