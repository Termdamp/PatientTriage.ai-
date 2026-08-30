import pytest
from app.engines.safety_engine import evaluate_safety
from app.utils.enums import Priority, AgeGroup

def test_critical_safety_low_spo2_and_low_bp():
    result = evaluate_safety(
        age=62, symptoms=["shortness_of_breath"], chief_complaint="Breathlessness",
        heart_rate=128, systolic_bp=85, diastolic_bp=52, spo2=89,
        temperature=38.2, respiratory_rate=30
    )
    assert result.triggered
    assert result.safety_floor == Priority.CRITICAL

def test_no_safety_flags_normal_vitals():
    result = evaluate_safety(
        age=35, symptoms=["headache"], chief_complaint="Headache",
        heart_rate=72, systolic_bp=120, diastolic_bp=80, spo2=98,
        temperature=36.8, respiratory_rate=14
    )
    assert result.safety_floor is None

def test_pediatric_safety_uses_pediatric_thresholds():
    result = evaluate_safety(
        age=8, symptoms=["fever", "shortness_of_breath"], chief_complaint="Fever",
        heart_rate=148, systolic_bp=90, diastolic_bp=58, spo2=93,
        temperature=39.2, respiratory_rate=34
    )
    assert result.age_group == AgeGroup.PEDIATRIC
    assert result.triggered

def test_geriatric_safety_uses_geriatric_thresholds():
    result = evaluate_safety(
        age=78, symptoms=["confusion"], chief_complaint="Confusion",
        heart_rate=98, systolic_bp=108, diastolic_bp=68, spo2=94,
        temperature=38.1, respiratory_rate=22
    )
    assert result.age_group == AgeGroup.GERIATRIC

def test_critical_symptom_triggers_flag():
    result = evaluate_safety(
        age=45, symptoms=["chest_pain", "shortness_of_breath"], chief_complaint="Chest pain",
        heart_rate=100, systolic_bp=105, diastolic_bp=70, spo2=95,
        temperature=37.0, respiratory_rate=20
    )
    assert result.triggered

def test_missing_history_does_not_lower_safety():
    """Missing history should NOT make safety floor lower."""
    result_with_history = evaluate_safety(
        age=55, symptoms=["shortness_of_breath"], chief_complaint="Shortness of breath",
        systolic_bp=88, spo2=91, respiratory_rate=28,
        history_available=True, medical_history=["hypertension"]
    )
    result_without_history = evaluate_safety(
        age=55, symptoms=["shortness_of_breath"], chief_complaint="Shortness of breath",
        systolic_bp=88, spo2=91, respiratory_rate=28,
        history_available=False, medical_history=None
    )
    # Missing history should not result in lower (safer) floor
    priority_order = {Priority.CRITICAL: 4, Priority.HIGH: 3, Priority.MODERATE: 2, Priority.LOW: 1, None: 0}
    assert priority_order.get(result_without_history.safety_floor, 0) >= priority_order.get(result_with_history.safety_floor, 0)
