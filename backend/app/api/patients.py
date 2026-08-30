from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.services.patient_service import get_all_patients, get_patient, get_latest_assessment, get_latest_vital
from app.services.audit_service import get_audit_events, create_audit_event
from app.schemas.patient import PatientResponse, PatientListItem
from app.schemas.audit import AuditListResponse, AuditEventResponse
from app.utils.enums import PatientStatus, EventType
from app.realtime.websocket_manager import manager
from app.realtime.events import WebSocketEvent
from datetime import timezone

router = APIRouter(prefix="/patients", tags=["patients"])

class PatientStatusUpdate(BaseModel):
    status: str  # WAITING, IN_REVIEW, IN_TREATMENT, COMPLETED
    reason: Optional[str] = None

def patient_to_dict(patient, db):
    assessment = get_latest_assessment(db, patient.id)
    vital = get_latest_vital(db, patient.id)
    arrival = patient.arrival_time
    if arrival and arrival.tzinfo is None:
        arrival = arrival.replace(tzinfo=timezone.utc)
    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "chiefComplaint": patient.chief_complaint,
        "symptoms": patient.symptoms or [],
        "medicalHistory": patient.medical_history,
        "historyAvailable": patient.history_available,
        "arrivalTime": arrival,
        "status": patient.status,
        "nextReassessmentDue": patient.next_reassessment_due,
        "bedId": patient.bed.id if patient.bed else None,
        "createdAt": patient.created_at,
        "updatedAt": patient.updated_at,
        "latestAssessment": {
            "id": assessment.id,
            "priority": assessment.priority.value,
            "riskScore": assessment.risk_score,
            "confidence": assessment.confidence,
            "safetyFlags": assessment.safety_flags or [],
            "reasons": assessment.reasons or [],
            "recommendedAction": assessment.recommended_action.value,
            "deteriorating": bool(assessment.deteriorating),
            "ageGroup": assessment.age_group,
            "explanation": assessment.explanation,
            "createdAt": assessment.created_at,
        } if assessment else None,
        "latestVitals": {
            "heartRate": vital.heart_rate,
            "systolicBp": vital.systolic_bp,
            "diastolicBp": vital.diastolic_bp,
            "spo2": vital.spo2,
            "temperature": vital.temperature,
            "respiratoryRate": vital.respiratory_rate,
            "timestamp": vital.timestamp,
        } if vital else None,
    }

@router.get("", response_model=List[dict])
def list_patients(status: Optional[str] = None, db: Session = Depends(get_db)):
    status_filter = PatientStatus(status) if status else None
    patients = get_all_patients(db, status=status_filter)
    return [patient_to_dict(p, db) for p in patients]

@router.get("/{patient_id}")
def get_patient_detail(patient_id: str, db: Session = Depends(get_db)):
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    result = patient_to_dict(patient, db)
    # Include vital history
    from app.models.vital import Vital
    from app.models.assessment import Assessment
    vitals = db.query(Vital).filter(Vital.patient_id == patient_id).order_by(Vital.timestamp.desc()).limit(20).all()
    assessments = db.query(Assessment).filter(Assessment.patient_id == patient_id).order_by(Assessment.created_at.desc()).limit(20).all()
    result["vitalHistory"] = [{
        "id": v.id, "heartRate": v.heart_rate, "systolicBp": v.systolic_bp,
        "diastolicBp": v.diastolic_bp, "spo2": v.spo2, "temperature": v.temperature,
        "respiratoryRate": v.respiratory_rate, "timestamp": v.timestamp
    } for v in vitals]
    result["assessmentHistory"] = [{
        "id": a.id, "priority": a.priority.value, "riskScore": a.risk_score,
        "confidence": a.confidence, "deteriorating": bool(a.deteriorating),
        "explanation": a.explanation,
        "createdAt": a.created_at
    } for a in assessments]
    return result

@router.get("/{patient_id}/audit")
def get_patient_audit(patient_id: str, db: Session = Depends(get_db)):
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    events = get_audit_events(db, patient_id=patient_id)
    return {"events": [{
        "id": e.id, "patientId": e.patient_id, "eventType": e.event_type,
        "actor": e.actor, "description": e.description,
        "metadata": e.metadata_, "createdAt": e.created_at
    } for e in events], "totalCount": len(events)}

@router.patch("/{patient_id}/status")
async def update_patient_status(patient_id: str, req: PatientStatusUpdate, db: Session = Depends(get_db)):
    """
    Directly change a patient's status — e.g. mark a patient treated/discharged
    (removing them from the triage queue) even if they were never assigned a bed.
    If the patient currently holds a bed and is being moved to COMPLETED or WAITING,
    the bed is released automatically.
    """
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    try:
        new_status = PatientStatus(req.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {req.status}")

    old_status = patient.status
    patient.status = new_status

    # Release any held bed when the patient leaves treatment/queue
    if patient.bed and new_status in (PatientStatus.COMPLETED, PatientStatus.WAITING):
        patient.bed.status = "AVAILABLE"
        patient.bed.patient_id = None

    create_audit_event(
        db, EventType.ASSESSMENT_UPDATED,
        f"Patient {patient.name} status changed: {old_status.value} → {new_status.value}"
        + (f". Reason: {req.reason}" if req.reason else ""),
        patient_id=patient.id,
        metadata={"oldStatus": old_status.value, "newStatus": new_status.value, "reason": req.reason}
    )
    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "patient_status_updated"})
    return {"status": "ok", "message": f"Patient {patient.name} marked as {new_status.value}"}
