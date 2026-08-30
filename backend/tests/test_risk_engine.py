import pytest
from app.engines.risk_engine import calculate_risk
from app.utils.enums import Priority

def test_critical_risk_score():
    result = calculate_risk(
        age=62, symptoms=["shortness_of_breath", "weakness"], chief_complaint="Breathlessness",
        heart_rate=128, systolic_bp=85, diastolic_bp=52, spo2=89,
        temperature=38.2, respiratory_rate=30
    )
    assert result.risk_score >= 75
    assert result.priority == Priority.CRITICAL

def test_low_risk_score():
    result = calculate_risk(
        age=30, symptoms=["laceration"], chief_complaint="Minor cut",
        heart_rate=72, systolic_bp=120, diastolic_bp=80, spo2=98,
        temperature=36.8, respiratory_rate=14
    )
    assert result.risk_score < 25
    assert result.priority == Priority.LOW

def test_high_risk_score():
    result = calculate_risk(
        age=55, symptoms=["chest_pain", "shortness_of_breath"], chief_complaint="Chest pain",
        heart_rate=110, systolic_bp=95, diastolic_bp=62, spo2=92,
        temperature=37.5, respiratory_rate=24,
        medical_history=["hypertension", "diabetes"], history_available=True
    )
    assert result.risk_score >= 50

def test_risk_factors_present():
    result = calculate_risk(
        age=62, symptoms=["shortness_of_breath"], chief_complaint="Breathlessness",
        spo2=88, systolic_bp=86
    )
    assert len(result.factors) > 0

def test_missing_history_not_zero_risk():
    result = calculate_risk(
        age=52, symptoms=["altered_mental_status"], chief_complaint="Unresponsive",
        heart_rate=122, systolic_bp=94, spo2=92, respiratory_rate=28,
        history_available=False, medical_history=None
    )
    assert result.risk_score >= 50
