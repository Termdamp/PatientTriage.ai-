import logging
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.assessment import Assessment
from app.schemas.triage import TriageRequest, TriageResponse, ReasonItem
from app.services.patient_service import (
    get_patient, create_patient, add_vital,
    get_latest_vital, get_previous_vital, get_latest_assessment
)
from app.services.audit_service import create_audit_event
from app.services.alert_service import save_alert
from app.engines.safety_engine import evaluate_safety
from app.engines.risk_engine import calculate_risk
from app.engines.confidence_engine import calculate_confidence
from app.engines.decision_engine import make_decision
from app.engines.deterioration_engine import detect_deterioration
from app.engines.alert_engine import generate_triage_alerts
from app.utils.enums import EventType, Priority
from app.utils.datetime import utcnow
from app.utils.ids import patient_id as generate_patient_id

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {Priority.CRITICAL: 4, Priority.HIGH: 3, Priority.MODERATE: 2, Priority.LOW: 1}

def vital_to_dict(vital) -> dict:
    """Convert Vital ORM object or VitalInput to dict."""
    if vital is None:
        return {}
    if hasattr(vital, 'heart_rate'):
        return {
            "heart_rate": vital.heart_rate,
            "systolic_bp": vital.systolic_bp,
            "diastolic_bp": vital.diastolic_bp,
            "spo2": vital.spo2,
            "temperature": vital.temperature,
            "respiratory_rate": vital.respiratory_rate,
        }
    return {}

def run_triage(
    db: Session,
    request: TriageRequest,
    forced_patient_id: Optional[str] = None
) -> TriageResponse:
    """Execute full triage pipeline."""
    with db.begin_nested():
        # 1. Get or create patient
        patient_id = forced_patient_id or request.patientId

        if patient_id:
            patient = get_patient(db, patient_id)
            if not patient:
                raise ValueError(f"Patient {patient_id} not found")
            # Update patient data
            patient.chief_complaint = request.chiefComplaint
            patient.symptoms = request.symptoms
            patient.updated_at = utcnow()
        else:
            # Prevent duplicate patient: check if there is an active patient with same Name, Age, Gender
            from app.models.patient import Patient
            from app.utils.enums import PatientStatus
            existing_active = db.query(Patient).filter(
                Patient.name == request.name,
                Patient.age == request.age,
                Patient.gender == request.gender,
                Patient.status != PatientStatus.COMPLETED
            ).first()

            if existing_active:
                patient = existing_active
                patient_id = patient.id
                patient.chief_complaint = request.chiefComplaint
                patient.symptoms = request.symptoms
                patient.updated_at = utcnow()
                create_audit_event(
                    db, EventType.PATIENT_CREATED,
                    f"Patient {patient.name} re-identified (active). Triggering reassessment.",
                    patient_id=patient_id
                )
            else:
                patient_id = generate_patient_id()
                patient = create_patient(
                    db=db,
                    patient_id=patient_id,
                    name=request.name or f"Patient-{patient_id[-4:]}",
                    age=request.age,
                    gender=request.gender,
                    chief_complaint=request.chiefComplaint,
                    symptoms=request.symptoms,
                    medical_history=request.medicalHistory,
                    history_available=request.historyAvailable,
                )
                create_audit_event(
                    db, EventType.PATIENT_CREATED,
                    f"New patient registered: {patient.name}",
                    patient_id=patient_id
                )

        # 2. Store new vitals
        prev_vital_orm = get_latest_vital(db, patient_id)
        prev_vital_dict = vital_to_dict(prev_vital_orm)

        vital = add_vital(db, patient_id, {
            "heartRate": request.vitals.heartRate,
            "systolicBp": request.vitals.systolicBp,
            "diastolicBp": request.vitals.diastolicBp,
            "spo2": request.vitals.spo2,
            "temperature": request.vitals.temperature,
            "respiratoryRate": request.vitals.respiratoryRate,
        })

        vitals = request.vitals

        # 3. Run engines
        safety_result = evaluate_safety(
            age=patient.age,
            symptoms=patient.symptoms or [],
            chief_complaint=patient.chief_complaint,
            heart_rate=vitals.heartRate,
            systolic_bp=vitals.systolicBp,
            diastolic_bp=vitals.diastolicBp,
            spo2=vitals.spo2,
            temperature=vitals.temperature,
            respiratory_rate=vitals.respiratoryRate,
            medical_history=patient.medical_history,
            history_available=patient.history_available,
        )

        prev_vitals_for_risk = {
            "spo2": prev_vital_dict.get("spo2"),
            "systolic_bp": prev_vital_dict.get("systolic_bp"),
        } if prev_vital_dict else None

        risk_result = calculate_risk(
            age=patient.age,
            symptoms=patient.symptoms or [],
            chief_complaint=patient.chief_complaint,
            heart_rate=vitals.heartRate,
            systolic_bp=vitals.systolicBp,
            diastolic_bp=vitals.diastolicBp,
            spo2=vitals.spo2,
            temperature=vitals.temperature,
            respiratory_rate=vitals.respiratoryRate,
            medical_history=patient.medical_history,
            history_available=patient.history_available,
            previous_vitals=prev_vitals_for_risk,
        )

        confidence_result = calculate_confidence(
            history_available=patient.history_available,
            medical_history=patient.medical_history,
            symptoms=patient.symptoms or [],
            chief_complaint=patient.chief_complaint,
            heart_rate=vitals.heartRate,
            systolic_bp=vitals.systolicBp,
            diastolic_bp=vitals.diastolicBp,
            spo2=vitals.spo2,
            temperature=vitals.temperature,
            respiratory_rate=vitals.respiratoryRate,
        )

        decision_result = make_decision(risk_result, safety_result, confidence_result)

        # 4. Deterioration detection
        from app.models.vital import Vital
        vitals_history_orm = db.query(Vital).filter(Vital.patient_id == patient_id).order_by(Vital.timestamp.asc()).all()
        vitals_history = [
            {
                "heart_rate": v.heart_rate,
                "systolic_bp": v.systolic_bp,
                "diastolic_bp": v.diastolic_bp,
                "spo2": v.spo2,
                "temperature": v.temperature,
                "respiratory_rate": v.respiratory_rate,
                "timestamp": v.timestamp
            }
            for v in vitals_history_orm
        ]

        det_result = detect_deterioration(vitals_history)
        deteriorating = det_result.deteriorating
        deterioration_severity = det_result.severity.value if det_result.deteriorating else None

        if deteriorating:
            create_audit_event(
                db, EventType.DETERIORATION_DETECTED,
                f"Deterioration detected for {patient.name}: {', '.join(det_result.changes[:2])}",
                patient_id=patient_id,
                metadata={"changes": det_result.changes, "score": det_result.score}
            )

        # Set next reassessment due time on Patient
        from datetime import timedelta
        reassessment_minutes = 120
        if decision_result.priority == Priority.CRITICAL:
            reassessment_minutes = 15
        elif decision_result.priority == Priority.HIGH:
            reassessment_minutes = 30
        elif decision_result.priority == Priority.MODERATE:
            reassessment_minutes = 60
        patient.next_reassessment_due = utcnow() + timedelta(minutes=reassessment_minutes)

        # Generate Qwen SLM explanation
        from app.services.llm_service import explain_decision
        explanation_data = {
            "patient_name": patient.name,
            "patient_age": patient.age,
            "patient_gender": patient.gender,
            "priority": decision_result.priority.value,
            "safety_floor": decision_result.safety_floor.value if decision_result.safety_floor else None,
            "safety_flags": safety_result.flags,
            "risk_score": decision_result.risk_score,
            "reasons": [{"code": r.code, "message": r.message} for r in decision_result.reasons],
            "deteriorating": deteriorating,
            "deterioration_severity": deterioration_severity
        }
        explanation_text = explain_decision(explanation_data)

        # 5. Save assessment
        assessment = Assessment(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            risk_score=decision_result.risk_score,
            priority=decision_result.priority,
            confidence=decision_result.confidence,
            safety_floor=decision_result.safety_floor,
            reasons=[{"code": r.code, "message": r.message} for r in decision_result.reasons],
            recommended_action=decision_result.recommended_action,
            model_version=decision_result.model_version,
            deteriorating=1 if deteriorating else 0,
            deterioration_severity=deterioration_severity,
            safety_flags=safety_result.flags,
            age_group=safety_result.age_group.value,
            data_quality=confidence_result.data_quality,
            explanation=explanation_text,
            created_at=utcnow()
        )
        db.add(assessment)
        db.flush()

        # 6. Get previous assessment for comparison
        prev_assessment = db.query(Assessment).filter(
            Assessment.patient_id == patient_id,
            Assessment.id != assessment.id
        ).order_by(Assessment.created_at.desc()).first()

        # 7. Generate alerts
        prev_priority = prev_assessment.priority if prev_assessment else None
        alert_candidates = generate_triage_alerts(
            patient_id=patient_id,
            patient_name=patient.name,
            priority=decision_result.priority,
            safety_flags=safety_result.flags,
            deteriorating=deteriorating,
            previous_priority=prev_priority
        )

        for candidate in alert_candidates:
            save_alert(db, candidate)
            create_audit_event(
                db, EventType.ALERT_CREATED,
                f"Alert: {candidate.message[:100]}",
                patient_id=patient_id,
                metadata={"alertType": candidate.type.value, "severity": candidate.severity.value}
            )

        # 8. Audit triage completion
        create_audit_event(
            db, EventType.TRIAGE_COMPLETED,
            f"Triage completed for {patient.name}: Priority={decision_result.priority.value}, Risk={decision_result.risk_score:.1f}",
            patient_id=patient_id,
            metadata={
                "priority": decision_result.priority.value,
                "riskScore": decision_result.risk_score,
                "confidence": decision_result.confidence,
                "safetyFlags": safety_result.flags
            }
        )

    return TriageResponse(
        patientId=patient_id,
        priority=decision_result.priority,
        riskScore=decision_result.risk_score,
        confidence=decision_result.confidence,
        confidenceLevel=confidence_result.confidence_level,
        safetyFloor=decision_result.safety_floor,
        safetyFlags=safety_result.flags,
        reasons=[ReasonItem(code=r.code, message=r.message) for r in decision_result.reasons],
        recommendedAction=decision_result.recommended_action,
        ageGroup=safety_result.age_group,
        dataQuality=confidence_result.data_quality,
        limitations=confidence_result.limitations,
        modelVersion=decision_result.model_version,
        deteriorating=deteriorating,
        deteriorationSeverity=deterioration_severity,
        explanation=explanation_text
    )

