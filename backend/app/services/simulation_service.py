import logging
from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session
from app.schemas.triage import TriageRequest
from app.schemas.vital import VitalInput
from app.services.triage_service import run_triage
from app.services.patient_service import get_patient, get_latest_vital
from app.services.capacity_service import update_capacity
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)

DETERIORATION_PROFILES = {
    # patient_id -> worsened vitals
    "default": {
        "spo2_drop": 6,
        "sbp_drop": 16,
        "hr_increase": 20,
        "rr_increase": 6,
    }
}

def simulate_deterioration(db: Session, patient_id: str) -> dict:
    """Simulate worsening vitals for a patient."""
    patient = get_patient(db, patient_id)
    if not patient:
        raise ValueError(f"Patient {patient_id} not found")

    latest_vital = get_latest_vital(db, patient_id)
    if not latest_vital:
        raise ValueError(f"No vitals found for patient {patient_id}")

    # Worsen vitals
    profile = DETERIORATION_PROFILES.get(patient_id, DETERIORATION_PROFILES["default"])

    new_spo2 = max(70, (latest_vital.spo2 or 95) - profile["spo2_drop"])
    new_sbp = max(60, (latest_vital.systolic_bp or 110) - profile["sbp_drop"])
    new_dbp = max(40, (latest_vital.diastolic_bp or 70) - 12)
    new_hr = min(180, (latest_vital.heart_rate or 90) + profile["hr_increase"])
    new_rr = min(45, (latest_vital.respiratory_rate or 18) + profile["rr_increase"])
    new_temp = latest_vital.temperature or 37.0

    triage_request = TriageRequest(
        patientId=patient_id,
        age=patient.age,
        gender=patient.gender,
        chiefComplaint=patient.chief_complaint,
        symptoms=patient.symptoms or [],
        historyAvailable=patient.history_available,
        medicalHistory=patient.medical_history,
        vitals=VitalInput(
            heartRate=new_hr,
            systolicBp=new_sbp,
            diastolicBp=new_dbp,
            spo2=new_spo2,
            temperature=new_temp,
            respiratoryRate=new_rr,
        )
    )

    result = run_triage(db, triage_request, forced_patient_id=patient_id)
    db.commit()

    return {
        "patientId": patient_id,
        "previousVitals": {
            "heartRate": latest_vital.heart_rate,
            "systolicBp": latest_vital.systolic_bp,
            "spo2": latest_vital.spo2,
            "respiratoryRate": latest_vital.respiratory_rate,
        },
        "newVitals": {
            "heartRate": new_hr,
            "systolicBp": new_sbp,
            "spo2": new_spo2,
            "respiratoryRate": new_rr,
        },
        "triageResult": result
    }

SURGE_SCENARIOS = {
    1: {"patientsPerHour": 10, "label": "NORMAL", "count": 1},
    2: {"patientsPerHour": 20, "label": "2X_SURGE", "count": 3},
    3: {"patientsPerHour": 30, "label": "3X_SURGE", "count": 5},
}

SURGE_PATIENTS = [
    {
        "name": "Sarah Connor", "age": 28, "gender": "female",
        "chiefComplaint": "Severe abdominal pain and fever",
        "symptoms": ["severe_abdominal_pain", "fever", "nausea"],
        "historyAvailable": True, "medicalHistory": ["appendectomy"],
        "vitals": {"heartRate": 105, "systolicBp": 112, "diastolicBp": 72, "spo2": 96, "temperature": 38.9, "respiratoryRate": 22}
    },
    {
        "name": "Marcus Wright", "age": 42, "gender": "male",
        "chiefComplaint": "Active bleeding from leg wound",
        "symptoms": ["major_trauma", "active_bleeding", "weakness"],
        "historyAvailable": False, "medicalHistory": [],
        "vitals": {"heartRate": 122, "systolicBp": 89, "diastolicBp": 50, "spo2": 93, "temperature": 36.6, "respiratoryRate": 28}
    },
    {
        "name": "Kyle Reese", "age": 19, "gender": "male",
        "chiefComplaint": "Shortness of breath and wheezing",
        "symptoms": ["severe_difficulty_breathing", "wheezing", "chest_tightness"],
        "historyAvailable": True, "medicalHistory": ["asthma"],
        "vitals": {"heartRate": 135, "systolicBp": 125, "diastolicBp": 80, "spo2": 89, "temperature": 37.1, "respiratoryRate": 32}
    },
    {
        "name": "John Connor", "age": 10, "gender": "male",
        "chiefComplaint": "Pediatric seizure, resolved but lethargic",
        "symptoms": ["altered_mental_status", "fatigue"],
        "historyAvailable": True, "medicalHistory": ["epilepsy"],
        "vitals": {"heartRate": 115, "systolicBp": 95, "diastolicBp": 60, "spo2": 95, "temperature": 37.8, "respiratoryRate": 24}
    },
    {
        "name": "Grace Harper", "age": 32, "gender": "female",
        "chiefComplaint": "Chest pain radiating to neck",
        "symptoms": ["chest_pain", "nausea", "palpitations"],
        "historyAvailable": True, "medicalHistory": [],
        "vitals": {"heartRate": 110, "systolicBp": 105, "diastolicBp": 68, "spo2": 94, "temperature": 37.2, "respiratoryRate": 20}
    }
]

def simulate_surge(db: Session, multiplier: int) -> dict:
    """Simulate an ED patient surge by inserting actual patient records and triaging them."""
    if multiplier not in [1, 2, 3]:
        raise ValueError("Multiplier must be 1, 2, or 3")

    scenario = SURGE_SCENARIOS[multiplier]
    patients_to_create = scenario["count"]
    
    from app.models.patient import Patient
    from app.models.bed import Bed
    from app.models.assessment import Assessment
    from app.utils.enums import PatientStatus, Priority, EventType
    from app.services.audit_service import create_audit_event
    import random
    import uuid

    created_patients = []
    
    # Draw patients from template
    sampled_templates = random.sample(SURGE_PATIENTS, min(patients_to_create, len(SURGE_PATIENTS)))
    
    for idx, temp in enumerate(sampled_templates):
        # Generate unique name slightly to prevent exact collisions
        uniq_name = f"{temp['name']} (Surge-{random.randint(100, 999)})"
        
        # Build Triage Request
        triage_req = TriageRequest(
            patientId=None,  # Brand new
            name=uniq_name,
            age=temp["age"],
            gender=temp["gender"],
            chiefComplaint=temp["chiefComplaint"],
            symptoms=temp["symptoms"],
            historyAvailable=temp["historyAvailable"],
            medicalHistory=temp["medicalHistory"],
            vitals=VitalInput(
                heartRate=temp["vitals"]["heartRate"],
                systolicBp=temp["vitals"]["systolicBp"],
                diastolicBp=temp["vitals"]["diastolicBp"],
                spo2=temp["vitals"]["spo2"],
                temperature=temp["vitals"]["temperature"],
                respiratoryRate=temp["vitals"]["respiratoryRate"]
            )
        )
        
        # Run standard triage pipeline
        res = run_triage(db, triage_req)
        
        # Fetch newly created Patient ORM object
        patient = db.query(Patient).filter(Patient.id == res.patientId).first()
        if patient:
            # Shift arrival time back slightly for wait calculations
            patient.arrival_time = utcnow() - timedelta(minutes=random.randint(5, 45))
            
            # Auto-allocate to beds if available
            assigned_bed_id = None
            if res.priority == Priority.CRITICAL:
                avail_bed = db.query(Bed).filter(Bed.type == "CRITICAL_CARE", Bed.status == "AVAILABLE").first()
                if avail_bed:
                    avail_bed.status = "OCCUPIED"
                    avail_bed.patient_id = patient.id
                    patient.status = PatientStatus.IN_TREATMENT
                    assigned_bed_id = avail_bed.id
            elif res.priority in [Priority.HIGH, Priority.MODERATE]:
                avail_bed = db.query(Bed).filter(Bed.type == "GENERAL", Bed.status == "AVAILABLE").first()
                if avail_bed:
                    avail_bed.status = "OCCUPIED"
                    avail_bed.patient_id = patient.id
                    patient.status = PatientStatus.IN_TREATMENT
                    assigned_bed_id = avail_bed.id
            
            if assigned_bed_id:
                create_audit_event(
                    db, EventType.CAPACITY_UPDATED,
                    f"Surge allocation: Patient {patient.name} assigned to Bed {assigned_bed_id}",
                    patient_id=patient.id,
                    metadata={"bedId": assigned_bed_id}
                )
                
            created_patients.append({
                "patientId": patient.id,
                "name": patient.name,
                "priority": res.priority.value,
                "riskScore": res.riskScore,
                "assignedBed": assigned_bed_id or "Lobby/Queue"
            })

    # Record surge start in audit log
    create_audit_event(
        db, EventType.SURGE_STARTED,
        f"ED Surge Simulation triggered: {scenario['label']} multiplier. Simulating {patients_to_create} incoming patients.",
        metadata={"multiplier": multiplier, "patientsSimulated": len(created_patients)}
    )

    # Recalculate capacity record
    occupied_beds_count = db.query(Bed).filter(Bed.status == "OCCUPIED").count()
    critical_occupied_count = db.query(Bed).filter(Bed.type == "CRITICAL_CARE", Bed.status == "OCCUPIED").count()
    
    # Update aggregates
    update_capacity(db, occupied_beds=occupied_beds_count, critical_occupied=critical_occupied_count)
    
    db.commit()

    active_count = db.query(Patient).filter(
        Patient.status.in_([PatientStatus.WAITING, PatientStatus.IN_REVIEW])
    ).count()

    # Count by priority
    from sqlalchemy import func
    subq = db.query(
        Assessment.patient_id,
        func.max(Assessment.created_at).label("max_ts")
    ).group_by(Assessment.patient_id).subquery()

    latest = db.query(Assessment).join(
        subq,
        (Assessment.patient_id == subq.c.patient_id) &
        (Assessment.created_at == subq.c.max_ts)
    ).all()

    priority_counts = {p: 0 for p in Priority}
    for a in latest:
        # Check if patient is active
        p = db.query(Patient).filter(Patient.id == a.patient_id).first()
        if p and p.status in [PatientStatus.WAITING, PatientStatus.IN_REVIEW]:
            priority_counts[a.priority] = priority_counts.get(a.priority, 0) + 1

    return {
        "mode": scenario["label"],
        "patientsPerHour": scenario["patientsPerHour"],
        "queueLength": active_count,
        "criticalPatients": priority_counts.get(Priority.CRITICAL, 0),
        "highPatients": priority_counts.get(Priority.HIGH, 0),
        "moderatePatients": priority_counts.get(Priority.MODERATE, 0),
        "capacityUtilization": round(occupied_beds_count / 50, 2),
        "simulatedPatients": created_patients
    }
