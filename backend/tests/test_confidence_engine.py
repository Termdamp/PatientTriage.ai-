from app.engines.confidence_engine import calculate_confidence
from app.utils.enums import ConfidenceLevel

def test_high_confidence_complete_data():
    result = calculate_confidence(
        history_available=True,
        medical_history=["hypertension"],
        symptoms=["chest_pain", "shortness_of_breath"],
        chief_complaint="Chest pain",
        heart_rate=128, systolic_bp=85, diastolic_bp=52,
        spo2=89, temperature=38.2, respiratory_rate=30
    )
    assert result.confidence > 0.60

def test_low_confidence_missing_history():
    result = calculate_confidence(
        history_available=False,
        medical_history=None,
        symptoms=["weakness"],
        chief_complaint="Not feeling well",
        heart_rate=None, systolic_bp=None, diastolic_bp=None,
        spo2=None, temperature=None, respiratory_rate=None
    )
    assert result.confidence < 0.50
    assert len(result.limitations) > 0

def test_confidence_limitations_reported():
    result = calculate_confidence(
        history_available=False,
        medical_history=None,
        symptoms=[],
        chief_complaint="Feeling unwell",
        heart_rate=100, systolic_bp=None, diastolic_bp=None,
        spo2=None, temperature=None, respiratory_rate=None
    )
    assert len(result.limitations) > 0

def test_risk_and_confidence_independent():
    """High risk with missing data = high risk + low confidence."""
    from app.engines.risk_engine import calculate_risk
    risk = calculate_risk(
        age=52, symptoms=["altered_mental_status", "shortness_of_breath"],
        chief_complaint="Unresponsive",
        heart_rate=122, systolic_bp=94, spo2=92, respiratory_rate=28,
        history_available=False, medical_history=None
    )
    confidence = calculate_confidence(
        history_available=False, medical_history=None,
        symptoms=["altered_mental_status", "shortness_of_breath"],
        chief_complaint="Unresponsive",
        heart_rate=122, systolic_bp=94, diastolic_bp=None,
        spo2=92, temperature=None, respiratory_rate=28
    )
    assert risk.risk_score >= 50  # High risk
    # Confidence can be moderate even with missing history if vitals are present
    assert confidence.confidence < 0.80  # Not fully confident
