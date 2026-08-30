"""
Seed database with synthetic patient data.

Run: python scripts/seed_database.py

This script:
1. Connects to PostgreSQL
2. Creates tables if they don't exist
3. Inserts synthetic patients with vitals
4. Runs initial triage assessments for each patient
5. Creates capacity record
6. Creates initial audit events
"""
import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.models.patient import Patient
from app.models.vital import Vital
from app.models.assessment import Assessment
from app.models.capacity import Capacity
from app.models.audit import AuditEvent
from app.models.bed import Bed
from app.models.resource import ResourceConfiguration
from app.services.llm_service import explain_decision
from app.engines.safety_engine import evaluate_safety
from app.engines.risk_engine import calculate_risk
from app.engines.confidence_engine import calculate_confidence
from app.engines.decision_engine import make_decision
from app.utils.enums import PatientStatus, EventType
from app.utils.datetime import utcnow
import uuid

def load_synthetic_data():
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'synthetic', 'patients.json')
    with open(data_path, 'r') as f:
        return json.load(f)

def assess_patient(patient_data: dict, vitals_data: dict):
    """Run engines and return assessment data."""
    safety = evaluate_safety(
        age=patient_data['age'],
        symptoms=patient_data.get('symptoms', []),
        chief_complaint=patient_data['chiefComplaint'],
        heart_rate=vitals_data.get('heartRate'),
        systolic_bp=vitals_data.get('systolicBp'),
        diastolic_bp=vitals_data.get('diastolicBp'),
        spo2=vitals_data.get('spo2'),
        temperature=vitals_data.get('temperature'),
        respiratory_rate=vitals_data.get('respiratoryRate'),
        medical_history=patient_data.get('medicalHistory') or [],
        history_available=patient_data.get('historyAvailable', True),
    )

    risk = calculate_risk(
        age=patient_data['age'],
        symptoms=patient_data.get('symptoms', []),
        chief_complaint=patient_data['chiefComplaint'],
        heart_rate=vitals_data.get('heartRate'),
        systolic_bp=vitals_data.get('systolicBp'),
        diastolic_bp=vitals_data.get('diastolicBp'),
        spo2=vitals_data.get('spo2'),
        temperature=vitals_data.get('temperature'),
        respiratory_rate=vitals_data.get('respiratoryRate'),
        medical_history=patient_data.get('medicalHistory') or [],
        history_available=patient_data.get('historyAvailable', True),
    )

    confidence = calculate_confidence(
        history_available=patient_data.get('historyAvailable', True),
        medical_history=patient_data.get('medicalHistory') or [],
        symptoms=patient_data.get('symptoms', []),
        chief_complaint=patient_data['chiefComplaint'],
        heart_rate=vitals_data.get('heartRate'),
        systolic_bp=vitals_data.get('systolicBp'),
        diastolic_bp=vitals_data.get('diastolicBp'),
        spo2=vitals_data.get('spo2'),
        temperature=vitals_data.get('temperature'),
        respiratory_rate=vitals_data.get('respiratoryRate'),
    )

    decision = make_decision(risk, safety, confidence)
    return safety, risk, confidence, decision

def seed():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    patients_data = load_synthetic_data()
    db = SessionLocal()

    try:
        # 1. Create beds
        print("Creating beds configuration...")
        beds = []
        # General Beds (BED-GEN-01 to BED-GEN-40)
        for i in range(1, 41):
            bed = Bed(id=f"BED-GEN-{i:02d}", type="GENERAL", status="AVAILABLE")
            db.add(bed)
            beds.append(bed)
        # ICU Beds (BED-ICU-01 to BED-ICU-10)
        for i in range(1, 11):
            bed = Bed(id=f"BED-ICU-{i:02d}", type="CRITICAL_CARE", status="AVAILABLE")
            db.add(bed)
            beds.append(bed)
        db.flush()

        # 2. Create resource configuration
        print("Seeding resource configuration...")
        res = ResourceConfiguration(
            doctors_total=5, doctors_active=3,
            nurses_total=12, nurses_active=8,
            ventilators_total=4, ventilators_active=1,
            monitors_total=8, monitors_active=2
        )
        db.add(res)
        db.flush()

        print(f"Seeding {len(patients_data)} patients...")
        now = utcnow()

        # Indexes for allocating beds
        gen_bed_idx = 1
        icu_bed_idx = 1

        for p_data in patients_data:
            patient_id = p_data['id']
            arrival_offset = p_data.get('arrivalOffsetMinutes', -30)
            arrival_time = now + timedelta(minutes=arrival_offset)

            # Determine next reassessment due time based on the priority of the patient
            # Run assessment engines first to know priority
            vitals_data = p_data['vitals']
            safety, risk, confidence, decision = assess_patient(p_data, vitals_data)

            # Reassessment interval
            from app.utils.enums import Priority
            reassessment_minutes = 120
            if decision.priority == Priority.CRITICAL:
                reassessment_minutes = 15
            elif decision.priority == Priority.HIGH:
                reassessment_minutes = 30
            elif decision.priority == Priority.MODERATE:
                reassessment_minutes = 60

            next_due = arrival_time + timedelta(minutes=reassessment_minutes)

            # Create patient
            patient = Patient(
                id=patient_id,
                name=p_data['name'],
                age=p_data['age'],
                gender=p_data['gender'],
                chief_complaint=p_data['chiefComplaint'],
                symptoms=p_data.get('symptoms', []),
                medical_history=p_data.get('medicalHistory') or [],
                history_available=p_data.get('historyAvailable', True),
                arrival_time=arrival_time,
                status=PatientStatus.WAITING,
                next_reassessment_due=next_due,
                created_at=arrival_time,
                updated_at=arrival_time
            )
            db.add(patient)
            db.flush()

            # Create initial vitals
            vital = Vital(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                heart_rate=vitals_data.get('heartRate'),
                systolic_bp=vitals_data.get('systolicBp'),
                diastolic_bp=vitals_data.get('diastolicBp'),
                spo2=vitals_data.get('spo2'),
                temperature=vitals_data.get('temperature'),
                respiratory_rate=vitals_data.get('respiratoryRate'),
                timestamp=arrival_time
            )
            db.add(vital)

            # Generate Qwen SLM Explanation
            explanation_data = {
                "patient_name": patient.name,
                "patient_age": patient.age,
                "patient_gender": patient.gender,
                "priority": decision.priority.value,
                "safety_floor": decision.safety_floor.value if decision.safety_floor else None,
                "safety_flags": safety.flags,
                "risk_score": decision.risk_score,
                "reasons": [{"code": r.code, "message": r.message} for r in decision.reasons],
                "deteriorating": False,
                "deterioration_severity": None
            }
            explanation_text = explain_decision(explanation_data)

            # Create assessment
            assessment = Assessment(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                risk_score=decision.risk_score,
                priority=decision.priority,
                confidence=decision.confidence,
                safety_floor=decision.safety_floor,
                reasons=[{'code': r.code, 'message': r.message} for r in decision.reasons],
                recommended_action=decision.recommended_action,
                model_version=decision.model_version,
                deteriorating=0,
                deterioration_severity=None,
                safety_flags=safety.flags,
                age_group=safety.age_group.value,
                data_quality=confidence.data_quality,
                explanation=explanation_text,
                created_at=arrival_time
            )
            db.add(assessment)

            # Map patient to a bed if they are active (status is not completed/discharged)
            # Let's say:
            # - Critical patients get BED-ICU-XX beds
            # - High and moderate patients get BED-GEN-XX beds
            # - Low priority patients wait (stay in WAITING without a bed)
            assigned_bed_id = None
            if decision.priority == Priority.CRITICAL:
                assigned_bed_id = f"BED-ICU-{icu_bed_idx:02d}"
                icu_bed_idx += 1
                patient.status = PatientStatus.IN_TREATMENT
            elif decision.priority in [Priority.HIGH, Priority.MODERATE]:
                assigned_bed_id = f"BED-GEN-{gen_bed_idx:02d}"
                gen_bed_idx += 1
                patient.status = PatientStatus.IN_TREATMENT

            if assigned_bed_id:
                bed_record = db.query(Bed).filter(Bed.id == assigned_bed_id).first()
                if bed_record:
                    bed_record.status = "OCCUPIED"
                    bed_record.patient_id = patient_id

            # Audit event
            audit = AuditEvent(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                event_type=EventType.PATIENT_CREATED,
                actor='SEED_SCRIPT',
                description=f'Patient {p_data["name"]} registered. Initial triage: {decision.priority.value}. Assigned Bed: {assigned_bed_id or "Lobby/Waiting"}',
                metadata_={'priority': decision.priority.value, 'riskScore': decision.risk_score, 'bedId': assigned_bed_id},
                created_at=arrival_time
            )
            db.add(audit)

            print(f"  {patient_id}: {p_data['name']} — Priority: {decision.priority.value} (Bed: {assigned_bed_id or 'None'})")

        # Create capacity record (aggregates for legacy compatibility)
        occupied_beds_count = db.query(Bed).filter(Bed.status == "OCCUPIED").count()
        critical_occupied_count = db.query(Bed).filter(Bed.type == "CRITICAL_CARE", Bed.status == "OCCUPIED").count()
        
        capacity = Capacity(
            id=str(uuid.uuid4()),
            total_beds=50,
            occupied_beds=occupied_beds_count,
            critical_beds=10,
            critical_occupied=critical_occupied_count,
            updated_at=now
        )
        db.add(capacity)

        db.commit()
        print(f"\nSeeding complete! {len(patients_data)} patients inserted.")
        print(f"Beds: 50 total. General: 40 (Occupied: {occupied_beds_count - critical_occupied_count}). Critical Care: 10 (Occupied: {critical_occupied_count}).")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    seed()
