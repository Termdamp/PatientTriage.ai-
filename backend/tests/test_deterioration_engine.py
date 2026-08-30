from app.engines.deterioration_engine import detect_deterioration
from app.utils.enums import DeteriorationSeverity

def test_significant_deterioration_detected():
    previous = {"heart_rate": 108, "systolic_bp": 101, "diastolic_bp": 65, "spo2": 95, "respiratory_rate": 24}
    current = {"heart_rate": 128, "systolic_bp": 85, "diastolic_bp": 52, "spo2": 89, "respiratory_rate": 30}
    result = detect_deterioration(previous, current)
    assert result.deteriorating is True
    assert result.severity in [DeteriorationSeverity.CRITICAL, DeteriorationSeverity.HIGH]
    assert len(result.changes) > 0

def test_stable_patient_no_deterioration():
    previous = {"heart_rate": 75, "systolic_bp": 120, "diastolic_bp": 80, "spo2": 98, "respiratory_rate": 14}
    current = {"heart_rate": 78, "systolic_bp": 118, "diastolic_bp": 78, "spo2": 97, "respiratory_rate": 15}
    result = detect_deterioration(previous, current)
    assert result.deteriorating is False
    assert result.severity == DeteriorationSeverity.STABLE

def test_multiple_worsening_vitals():
    previous = {"heart_rate": 90, "systolic_bp": 115, "spo2": 96, "respiratory_rate": 18}
    current = {"heart_rate": 130, "systolic_bp": 85, "spo2": 87, "respiratory_rate": 32}
    result = detect_deterioration(previous, current)
    assert result.deteriorating is True
    assert result.score >= 40  # Multiple critical changes

def test_partial_vitals_deterioration():
    """Deterioration should work even with missing some vitals."""
    previous = {"spo2": 97}
    current = {"spo2": 88}
    result = detect_deterioration(previous, current)
    assert result.deteriorating is True
