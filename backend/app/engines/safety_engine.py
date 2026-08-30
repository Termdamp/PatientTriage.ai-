"""
Safety Engine - Deterministic safety rule evaluation.

This engine identifies critical safety conditions that must establish a
minimum priority floor regardless of the risk score.

DISCLAIMER: Prototype thresholds. NOT clinically validated.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from app.utils.enums import Priority, AgeGroup

# --- Safety thresholds (NOT clinically validated - prototype only) ---

ADULT_THRESHOLDS = {
    "spo2_critical": 90,
    "spo2_warning": 94,
    "systolic_bp_critical": 90,
    "systolic_bp_warning": 100,
    "heart_rate_critical_high": 130,
    "heart_rate_critical_low": 40,
    "heart_rate_warning_high": 110,
    "heart_rate_warning_low": 55,
    "respiratory_rate_critical": 30,
    "respiratory_rate_warning": 24,
    "temperature_critical_high": 40.0,
    "temperature_critical_low": 35.0,
}

PEDIATRIC_THRESHOLDS = {
    "spo2_critical": 92,
    "spo2_warning": 95,
    "systolic_bp_critical": 70,
    "systolic_bp_warning": 80,
    "heart_rate_critical_high": 180,
    "heart_rate_critical_low": 60,
    "heart_rate_warning_high": 160,
    "heart_rate_warning_low": 70,
    "respiratory_rate_critical": 40,
    "respiratory_rate_warning": 30,
    "temperature_critical_high": 39.5,
    "temperature_critical_low": 35.5,
}

GERIATRIC_THRESHOLDS = {
    "spo2_critical": 91,
    "spo2_warning": 95,
    "systolic_bp_critical": 100,  # Higher threshold for geriatric
    "systolic_bp_warning": 110,
    "heart_rate_critical_high": 120,
    "heart_rate_critical_low": 45,
    "heart_rate_warning_high": 100,
    "heart_rate_warning_low": 55,
    "respiratory_rate_critical": 28,
    "respiratory_rate_warning": 22,
    "temperature_critical_high": 39.5,
    "temperature_critical_low": 35.0,
}

def get_age_group(age: int) -> AgeGroup:
    if age < 18:
        return AgeGroup.PEDIATRIC
    elif age >= 65:
        return AgeGroup.GERIATRIC
    else:
        return AgeGroup.ADULT

def get_thresholds(age_group: AgeGroup) -> Dict[str, float]:
    if age_group == AgeGroup.PEDIATRIC:
        return PEDIATRIC_THRESHOLDS
    elif age_group == AgeGroup.GERIATRIC:
        return GERIATRIC_THRESHOLDS
    else:
        return ADULT_THRESHOLDS

@dataclass
class SafetyResult:
    triggered: bool
    safety_floor: Optional[Priority]
    flags: List[str]
    age_group: AgeGroup
    flag_details: List[Dict[str, Any]] = field(default_factory=list)

# Critical symptoms that alone can trigger safety floor
CRITICAL_SYMPTOMS = {
    "chest_pain", "chest_tightness",
    "loss_of_consciousness", "unconscious", "syncope",
    "severe_difficulty_breathing", "respiratory_arrest",
    "cardiac_arrest", "anaphylaxis",
    "stroke_symptoms", "facial_droop", "arm_weakness",
    "major_trauma", "active_bleeding",
    "seizure_active", "status_epilepticus"
}

HIGH_RISK_SYMPTOMS = {
    "shortness_of_breath", "difficulty_breathing",
    "severe_abdominal_pain", "weakness",
    "altered_mental_status", "confusion",
    "severe_headache", "worst_headache",
    "palpitations", "irregular_heartbeat"
}

def evaluate_safety(
    age: int,
    symptoms: List[str],
    chief_complaint: str,
    heart_rate: Optional[float] = None,
    systolic_bp: Optional[float] = None,
    diastolic_bp: Optional[float] = None,
    spo2: Optional[float] = None,
    temperature: Optional[float] = None,
    respiratory_rate: Optional[float] = None,
    medical_history: Optional[List[str]] = None,
    history_available: bool = True,
) -> SafetyResult:
    """Evaluate safety rules and return safety floor."""
    age_group = get_age_group(age)
    thresholds = get_thresholds(age_group)
    flags = []
    flag_details = []
    critical_count = 0
    high_count = 0

    # Normalize symptoms and complaint for matching
    all_symptoms = set(s.lower() for s in symptoms)
    complaint_lower = chief_complaint.lower()

    # --- SpO2 evaluation ---
    if spo2 is not None:
        if spo2 < thresholds["spo2_critical"]:
            flags.append("LOW_OXYGEN_SATURATION_CRITICAL")
            flag_details.append({"flag": "LOW_OXYGEN_SATURATION_CRITICAL", "value": spo2, "threshold": thresholds["spo2_critical"]})
            critical_count += 1
        elif spo2 < thresholds["spo2_warning"]:
            flags.append("LOW_OXYGEN_SATURATION")
            flag_details.append({"flag": "LOW_OXYGEN_SATURATION", "value": spo2, "threshold": thresholds["spo2_warning"]})
            high_count += 1

    # --- Blood pressure evaluation ---
    if systolic_bp is not None:
        if systolic_bp < thresholds["systolic_bp_critical"]:
            flags.append("LOW_BLOOD_PRESSURE_CRITICAL")
            flag_details.append({"flag": "LOW_BLOOD_PRESSURE_CRITICAL", "value": systolic_bp, "threshold": thresholds["systolic_bp_critical"]})
            critical_count += 1
        elif systolic_bp < thresholds["systolic_bp_warning"]:
            flags.append("LOW_BLOOD_PRESSURE")
            flag_details.append({"flag": "LOW_BLOOD_PRESSURE", "value": systolic_bp, "threshold": thresholds["systolic_bp_warning"]})
            high_count += 1
        elif systolic_bp > 180:
            flags.append("HIGH_BLOOD_PRESSURE")
            flag_details.append({"flag": "HIGH_BLOOD_PRESSURE", "value": systolic_bp})
            high_count += 1

    # --- Heart rate evaluation ---
    if heart_rate is not None:
        if heart_rate > thresholds["heart_rate_critical_high"] or heart_rate < thresholds["heart_rate_critical_low"]:
            flags.append("CRITICAL_HEART_RATE")
            flag_details.append({"flag": "CRITICAL_HEART_RATE", "value": heart_rate})
            critical_count += 1
        elif heart_rate > thresholds["heart_rate_warning_high"] or heart_rate < thresholds["heart_rate_warning_low"]:
            flags.append("ABNORMAL_HEART_RATE")
            flag_details.append({"flag": "ABNORMAL_HEART_RATE", "value": heart_rate})
            high_count += 1

    # --- Respiratory rate evaluation ---
    if respiratory_rate is not None:
        if respiratory_rate > thresholds["respiratory_rate_critical"]:
            flags.append("RESPIRATORY_DISTRESS_CRITICAL")
            flag_details.append({"flag": "RESPIRATORY_DISTRESS_CRITICAL", "value": respiratory_rate})
            critical_count += 1
        elif respiratory_rate > thresholds["respiratory_rate_warning"]:
            flags.append("RESPIRATORY_DISTRESS")
            flag_details.append({"flag": "RESPIRATORY_DISTRESS", "value": respiratory_rate})
            high_count += 1

    # --- Temperature evaluation ---
    if temperature is not None:
        if temperature > thresholds["temperature_critical_high"] or temperature < thresholds["temperature_critical_low"]:
            flags.append("CRITICAL_TEMPERATURE")
            flag_details.append({"flag": "CRITICAL_TEMPERATURE", "value": temperature})
            critical_count += 1

    # --- Symptom evaluation ---
    for symptom in CRITICAL_SYMPTOMS:
        if symptom in all_symptoms or symptom in complaint_lower:
            flags.append(f"CRITICAL_SYMPTOM_{symptom.upper()}")
            critical_count += 1
            break

    for symptom in HIGH_RISK_SYMPTOMS:
        if symptom in all_symptoms:
            high_count += 1

    # --- Medical history modifiers ---
    if medical_history:
        high_risk_history = {"heart_failure", "copd", "coronary_artery_disease", "diabetes", "chronic_kidney_disease"}
        for condition in high_risk_history:
            if any(condition in h.lower() for h in medical_history):
                high_count += 1

    # Geriatric additional risk
    if age_group == AgeGroup.GERIATRIC and age >= 80:
        high_count += 1

    # --- Determine safety floor ---
    # Multiple critical vitals = CRITICAL floor
    if critical_count >= 2:
        safety_floor = Priority.CRITICAL
    elif critical_count == 1 and high_count >= 1:
        safety_floor = Priority.CRITICAL
    elif critical_count == 1:
        safety_floor = Priority.HIGH
    elif high_count >= 3:
        safety_floor = Priority.HIGH
    elif high_count >= 1:
        safety_floor = Priority.MODERATE
    else:
        safety_floor = None

    # Clean up flag names for display
    display_flags = list(set(flags))

    return SafetyResult(
        triggered=len(flags) > 0,
        safety_floor=safety_floor,
        flags=display_flags,
        age_group=age_group,
        flag_details=flag_details
    )
