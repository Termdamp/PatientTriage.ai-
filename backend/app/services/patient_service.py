import logging
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.vital import Vital
from app.models.assessment import Assessment
from app.models.override import Override
from app.utils.enums import PatientStatus
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)

def get_patient(db: Session, patient_id: str) -> Optional[Patient]:
    return db.query(Patient).filter(Patient.id == patient_id).first()

def get_all_patients(db: Session, status: Optional[PatientStatus] = None) -> List[Patient]:
    query = db.query(Patient)
    if status:
        query = query.filter(Patient.status == status)
    return query.order_by(Patient.arrival_time.desc()).all()

def create_patient(
    db: Session,
    patient_id: str,
    name: str,
    age: int,
    gender: str,
    chief_complaint: str,
    symptoms: List[str],
    medical_history: Optional[List[str]],
    history_available: bool,
    arrival_time=None
) -> Patient:
    patient = Patient(
        id=patient_id,
        name=name,
        age=age,
        gender=gender,
        chief_complaint=chief_complaint,
        symptoms=symptoms,
        medical_history=medical_history or [],
        history_available=history_available,
        arrival_time=arrival_time or utcnow(),
        status=PatientStatus.WAITING,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    db.add(patient)
    db.flush()
    return patient

def add_vital(db: Session, patient_id: str, vital_data: dict) -> Vital:
    vital = Vital(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        heart_rate=vital_data.get("heartRate"),
        systolic_bp=vital_data.get("systolicBp"),
        diastolic_bp=vital_data.get("diastolicBp"),
        spo2=vital_data.get("spo2"),
        temperature=vital_data.get("temperature"),
        respiratory_rate=vital_data.get("respiratoryRate"),
        timestamp=utcnow()
    )
    db.add(vital)
    db.flush()
    return vital

def get_latest_vital(db: Session, patient_id: str) -> Optional[Vital]:
    return db.query(Vital).filter(Vital.patient_id == patient_id).order_by(Vital.timestamp.desc()).first()

def get_previous_vital(db: Session, patient_id: str) -> Optional[Vital]:
    """Get the second-most-recent vital (for deterioration detection)."""
    vitals = db.query(Vital).filter(Vital.patient_id == patient_id).order_by(Vital.timestamp.desc()).limit(2).all()
    return vitals[1] if len(vitals) >= 2 else None

def get_latest_assessment(db: Session, patient_id: str) -> Optional[Assessment]:
    return db.query(Assessment).filter(Assessment.patient_id == patient_id).order_by(Assessment.created_at.desc()).first()

def get_active_override(db: Session, patient_id: str) -> Optional[Override]:
    return db.query(Override).filter(Override.patient_id == patient_id).order_by(Override.created_at.desc()).first()
