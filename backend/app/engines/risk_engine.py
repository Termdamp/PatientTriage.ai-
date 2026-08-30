"""
Risk Engine - Deterministic risk score calculation.

Calculates a risk score 0-100 based on vitals, symptoms, history, and age.
DISCLAIMER: Prototype scoring. NOT clinically validated.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from app.utils.enums import Priority, AgeGroup
from app.engines.safety_engine import get_age_group

@dataclass
class RiskFactor:
    name: str
    contribution: float
    description: str

@dataclass
class RiskResult:
    risk_score: float  # 0-100
    priority: Priority
    factors: List[RiskFactor]
    age_group: AgeGroup

def risk_score_to_priority(score: float) -> Priority:
    if score >= 75:
        return Priority.CRITICAL
    elif score >= 50:
        return Priority.HIGH
    elif score >= 25:
        return Priority.MODERATE
    else:
        return Priority.LOW

def calculate_vital_risk(
    heart_rate: Optional[float],
    systolic_bp: Optional[float],
    diastolic_bp: Optional[float],
    spo2: Optional[float],
    temperature: Optional[float],
    respiratory_rate: Optional[float],
    age_group: AgeGroup
) -> Tuple[float, List[RiskFactor]]:
    """Calculate risk score contribution from vitals."""
    score = 0.0
    factors = []

    # SpO2 scoring (max 25 points)
    if spo2 is not None:
        if spo2 < 85:
            contrib = 25
            factors.append(RiskFactor("low_oxygen_saturation", contrib, f"SpO2 critically low at {spo2}%"))
        elif spo2 < 90:
            contrib = 20
            factors.append(RiskFactor("low_oxygen_saturation", contrib, f"SpO2 severely low at {spo2}%"))
        elif spo2 < 94:
            contrib = 12
            factors.append(RiskFactor("low_oxygen_saturation", contrib, f"SpO2 below normal at {spo2}%"))
        elif spo2 < 96:
            contrib = 5
            factors.append(RiskFactor("low_oxygen_saturation", contrib, f"SpO2 borderline at {spo2}%"))
        else:
            contrib = 0
        score += contrib

    # Blood pressure scoring (max 20 points)
    bp_threshold_critical = 90 if age_group != AgeGroup.GERIATRIC else 100
    bp_threshold_warning = 100 if age_group != AgeGroup.GERIATRIC else 110

    if systolic_bp is not None:
        if systolic_bp < bp_threshold_critical:
            contrib = 20
            factors.append(RiskFactor("low_blood_pressure", contrib, f"Systolic BP critically low at {systolic_bp}mmHg"))
        elif systolic_bp < bp_threshold_warning:
            contrib = 15
            factors.append(RiskFactor("low_blood_pressure", contrib, f"Systolic BP low at {systolic_bp}mmHg"))
        elif systolic_bp > 180:
            contrib = 10
            factors.append(RiskFactor("high_blood_pressure", contrib, f"Systolic BP elevated at {systolic_bp}mmHg"))
        else:
            contrib = 0
        score += contrib

    # Heart rate scoring (max 15 points)
    hr_max = 130 if age_group == AgeGroup.ADULT else (180 if age_group == AgeGroup.PEDIATRIC else 120)
    if heart_rate is not None:
        if heart_rate > hr_max or heart_rate < 40:
            contrib = 15
            factors.append(RiskFactor("abnormal_heart_rate", contrib, f"Heart rate critically abnormal at {heart_rate}bpm"))
        elif heart_rate > 110 or heart_rate < 50:
            contrib = 10
            factors.append(RiskFactor("abnormal_heart_rate", contrib, f"Heart rate abnormal at {heart_rate}bpm"))
        elif heart_rate > 100:
            contrib = 5
            factors.append(RiskFactor("elevated_heart_rate", contrib, f"Heart rate mildly elevated at {heart_rate}bpm"))
        else:
            contrib = 0
        score += contrib

    # Respiratory rate scoring (max 20 points)
    rr_critical = 30 if age_group != AgeGroup.PEDIATRIC else 40
    rr_warning = 24 if age_group != AgeGroup.PEDIATRIC else 30
    if respiratory_rate is not None:
        if respiratory_rate > rr_critical:
            contrib = 20
            factors.append(RiskFactor("respiratory_distress", contrib, f"Respiratory rate critically elevated at {respiratory_rate}/min"))
        elif respiratory_rate > rr_warning:
            contrib = 12
            factors.append(RiskFactor("respiratory_distress", contrib, f"Respiratory rate elevated at {respiratory_rate}/min"))
        elif respiratory_rate < 10:
            contrib = 15
            factors.append(RiskFactor("low_respiratory_rate", contrib, f"Respiratory rate dangerously low at {respiratory_rate}/min"))
        else:
            contrib = 0
        score += contrib

    # Temperature scoring (max 8 points)
    if temperature is not None:
        if temperature > 40.0 or temperature < 35.0:
            contrib = 8
            factors.append(RiskFactor("critical_temperature", contrib, f"Temperature critically abnormal at {temperature}°C"))
        elif temperature > 38.5:
            contrib = 5
            factors.append(RiskFactor("fever", contrib, f"Significant fever at {temperature}°C"))
        elif temperature > 37.5:
            contrib = 2
            factors.append(RiskFactor("fever", contrib, f"Low-grade fever at {temperature}°C"))
        else:
            contrib = 0
        score += contrib

    return min(score, 70.0), factors  # Vitals max 70 points

SYMPTOM_SCORES = {
    "chest_pain": 15, "chest_tightness": 12,
    "loss_of_consciousness": 15, "syncope": 12,
    "shortness_of_breath": 12, "severe_difficulty_breathing": 15,
    "altered_mental_status": 12, "confusion": 10,
    "severe_headache": 8, "worst_headache": 12,
    "weakness": 8, "arm_weakness": 10,
    "facial_droop": 12, "stroke_symptoms": 15,
    "palpitations": 6,
    "nausea": 3, "vomiting": 4,
    "abdominal_pain": 5, "severe_abdominal_pain": 10,
    "dizziness": 5, "headache": 4,
    "fever": 3, "cough": 3,
    "fatigue": 3, "back_pain": 4,
}

HISTORY_SCORES = {
    "heart_failure": 10, "congestive_heart_failure": 10,
    "coronary_artery_disease": 8, "previous_mi": 8, "myocardial_infarction": 8,
    "copd": 8, "asthma": 5,
    "diabetes": 5, "hypertension": 4,
    "chronic_kidney_disease": 6, "renal_failure": 8,
    "stroke": 7, "tia": 5,
    "cancer": 6, "immunocompromised": 7,
    "liver_disease": 6, "cirrhosis": 8,
    "anticoagulation": 5, "bleeding_disorder": 5,
}

def calculate_risk(
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
    previous_vitals: Optional[Dict] = None,
) -> RiskResult:
    """Calculate deterministic risk score."""
    age_group = get_age_group(age)
    all_factors: List[RiskFactor] = []

    # 1. Vital risk (up to 70 points)
    vital_score, vital_factors = calculate_vital_risk(
        heart_rate, systolic_bp, diastolic_bp, spo2, temperature, respiratory_rate, age_group
    )
    all_factors.extend(vital_factors)

    # 2. Symptom risk (up to 20 points)
    symptom_score = 0.0
    symptom_set = set(s.lower() for s in symptoms)
    chief_words = set(chief_complaint.lower().split())

    for symptom, contrib in sorted(SYMPTOM_SCORES.items(), key=lambda x: -x[1]):
        if symptom in symptom_set:
            symptom_score += contrib
            all_factors.append(RiskFactor("symptom", contrib, f"Reported symptom: {symptom.replace('_', ' ')}"))

    symptom_score = min(symptom_score, 20.0)

    # 3. History risk (up to 15 points)
    history_score = 0.0
    if history_available and medical_history:
        history_lower = " ".join(h.lower() for h in medical_history)
        for condition, contrib in sorted(HISTORY_SCORES.items(), key=lambda x: -x[1]):
            if condition in history_lower:
                history_score += contrib
                all_factors.append(RiskFactor("medical_history", contrib, f"Relevant history: {condition.replace('_', ' ')}"))
    elif not history_available:
        # Unknown history adds moderate risk — we don't know what we don't know
        history_score = 5.0
        all_factors.append(RiskFactor("unknown_history", 5.0, "Medical history unavailable — treating conservatively"))

    history_score = min(history_score, 15.0)

    # 4. Age modifier
    age_score = 0.0
    if age >= 80:
        age_score = 8.0
        all_factors.append(RiskFactor("age_geriatric_advanced", age_score, f"Advanced age ({age}y) increases risk"))
    elif age >= 65:
        age_score = 5.0
        all_factors.append(RiskFactor("age_geriatric", age_score, f"Geriatric patient ({age}y)"))
    elif age < 5:
        age_score = 6.0
        all_factors.append(RiskFactor("age_infant", age_score, f"Infant/toddler ({age}y) — higher vulnerability"))
    elif age < 18:
        age_score = 3.0
        all_factors.append(RiskFactor("age_pediatric", age_score, f"Pediatric patient ({age}y)"))

    # 5. Trajectory (if previous vitals provided)
    trajectory_score = 0.0
    if previous_vitals:
        if spo2 is not None and previous_vitals.get("spo2"):
            delta = previous_vitals["spo2"] - spo2
            if delta > 5:
                trajectory_score += 8
                all_factors.append(RiskFactor("deteriorating_spo2", 8, f"SpO2 decreased by {delta:.1f}%"))
        if systolic_bp is not None and previous_vitals.get("systolic_bp"):
            delta = previous_vitals["systolic_bp"] - systolic_bp
            if delta > 15:
                trajectory_score += 6
                all_factors.append(RiskFactor("deteriorating_bp", 6, f"BP dropped by {delta:.1f}mmHg"))

    trajectory_score = min(trajectory_score, 15.0)

    # Total score
    total = vital_score + symptom_score + history_score + age_score + trajectory_score
    total = min(100.0, max(0.0, total))

    priority = risk_score_to_priority(total)

    # Sort factors by contribution descending
    all_factors.sort(key=lambda f: -f.contribution)

    return RiskResult(
        risk_score=round(total, 1),
        priority=priority,
        factors=all_factors[:10],  # Top 10 factors
        age_group=age_group
    )
