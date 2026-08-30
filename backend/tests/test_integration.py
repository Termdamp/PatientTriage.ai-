import pytest
from sqlalchemy.orm import Session
from app.services.triage_service import run_triage
from app.schemas.triage import TriageRequest
from app.schemas.vital import VitalInput
from app.services.simulation_service import simulate_deterioration
from app.services.patient_service import get_latest_assessment
from app.services.alert_service import get_alerts
from app.services.audit_service import get_audit_events
from app.utils.enums import Priority

def create_p009_request(vitals: VitalInput) -> TriageRequest:
    return TriageRequest(
        name="Carlos Rivera",
        age=62,
        gender="male",
        chiefComplaint="Breathlessness and weakness",
        symptoms=["shortness_of_breath", "weakness", "palpitations"],
        historyAvailable=True,
        medicalHistory=["hypertension", "heart_failure"],
        vitals=vitals
    )

def test_full_triage_to_deterioration_flow(db: Session):
    """
    Integration test: P009 initial assessment (HIGH) → deterioration → CRITICAL
    This is the key demo scenario.
    """
    # Step 1: Initial triage
    initial_vitals = VitalInput(
        heartRate=108, systolicBp=101, diastolicBp=65,
        spo2=95, temperature=37.8, respiratoryRate=24
    )
    initial_request = create_p009_request(initial_vitals)
    initial_result = run_triage(db, initial_request)
    db.commit()

    patient_id = initial_result.patientId

    # Verify initial state
    assert initial_result.priority in [Priority.HIGH, Priority.MODERATE, Priority.CRITICAL]
    initial_priority = initial_result.priority

    # Step 2: Simulate deterioration
    result = simulate_deterioration(db, patient_id)
    triage = result["triageResult"]

    # Verify deterioration outcome
    assert triage.deteriorating is True
    assert triage.priority == Priority.CRITICAL

    # Step 3: Check that audit events were created
    events = get_audit_events(db, patient_id=patient_id)
    event_types = [e.event_type for e in events]
    assert "PATIENT_CREATED" in event_types
    assert "DETERIORATION_DETECTED" in event_types or "TRIAGE_COMPLETED" in event_types

    # Step 4: Check alerts were created
    alerts = get_alerts(db)
    patient_alerts = [a for a in alerts if a.patient_id == patient_id]
    assert len(patient_alerts) > 0

def test_clinician_override_flow(db: Session):
    from app.models.override import Override
    from app.utils.enums import Priority
    import uuid

    # Create a patient
    vitals = VitalInput(heartRate=118, systolicBp=88, diastolicBp=56, spo2=91, temperature=37.1, respiratoryRate=26)
    request = TriageRequest(
        name="Test Override Patient",
        age=58, gender="female",
        chiefComplaint="Chest pain",
        symptoms=["chest_pain", "shortness_of_breath"],
        historyAvailable=True, medicalHistory=["hypertension"],
        vitals=vitals
    )
    result = run_triage(db, request)
    db.commit()

    # Override to HIGH
    assessment = get_latest_assessment(db, result.patientId)
    override = Override(
        id=str(uuid.uuid4()),
        patient_id=result.patientId,
        assessment_id=assessment.id,
        original_priority=assessment.priority,
        new_priority=Priority.HIGH,
        reason="Clinician assessment indicates stable condition",
        clinician_id="CLINICIAN_DEMO"
    )
    db.add(override)
    db.commit()

    # Verify override was stored
    stored = db.query(Override).filter(Override.patient_id == result.patientId).first()
    assert stored is not None
    assert stored.new_priority == Priority.HIGH
    assert stored.original_priority == result.priority

def test_missing_history_not_low_risk(db: Session):
    """Missing history should not result in LOW risk for symptomatic patient."""
    vitals = VitalInput(heartRate=122, systolicBp=94, diastolicBp=60, spo2=92, temperature=38.5, respiratoryRate=28)
    request = TriageRequest(
        name="Unknown Trauma Patient",
        age=35, gender="male",
        chiefComplaint="Unresponsive major trauma",
        symptoms=["altered_mental_status", "shortness_of_breath", "major_trauma"],
        historyAvailable=False, medicalHistory=None,
        vitals=vitals
    )
    result = run_triage(db, request)
    db.commit()
    assert result.priority != Priority.LOW
    assert result.confidence < 0.90  # Should have reduced confidence
