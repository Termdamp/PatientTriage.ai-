import logging
from typing import List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.override import Override
from app.engines.queue_engine import QueueEntry, build_queue
from app.utils.enums import PatientStatus, Priority
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)

def get_queue(db: Session) -> List[QueueEntry]:
    """Build and return the current patient queue."""
    # Get all waiting/in-review patients
    active_patients = db.query(Patient).filter(
        Patient.status.in_([PatientStatus.WAITING, PatientStatus.IN_REVIEW])
    ).all()

    entries = []
    for patient in active_patients:
        # Get latest assessment
        latest_assessment = db.query(Assessment).filter(
            Assessment.patient_id == patient.id
        ).order_by(Assessment.created_at.desc()).first()

        if latest_assessment is None:
            continue  # Skip patients without assessment

        # Get latest override
        latest_override = db.query(Override).filter(
            Override.patient_id == patient.id
        ).order_by(Override.created_at.desc()).first()

        entry = QueueEntry(
            patient_id=patient.id,
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            chief_complaint=patient.chief_complaint,
            priority=latest_assessment.priority,
            risk_score=latest_assessment.risk_score,
            confidence=latest_assessment.confidence,
            arrival_time=patient.arrival_time if patient.arrival_time.tzinfo else patient.arrival_time.replace(tzinfo=timezone.utc),
            deteriorating=bool(latest_assessment.deteriorating),
            safety_flags=latest_assessment.safety_flags or [],
            reasons=latest_assessment.reasons or [],
            recommended_action=latest_assessment.recommended_action.value if latest_assessment.recommended_action else "CLINICIAN_REVIEW",
            override_priority=latest_override.new_priority if latest_override else None,
        )
        entries.append(entry)

    sorted_entries = build_queue(entries)
    return sorted_entries
