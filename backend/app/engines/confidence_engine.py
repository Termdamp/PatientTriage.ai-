"""
Confidence Engine - Quantifies reliability of the assessment.

IMPORTANT: Risk and Confidence are INDEPENDENT dimensions.
High risk + Low confidence = valid and important state.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from app.utils.enums import ConfidenceLevel

@dataclass
class ConfidenceResult:
    confidence: float  # 0.0 - 1.0
    confidence_level: ConfidenceLevel
    limitations: List[str]
    data_quality: float  # 0.0 - 1.0

def calculate_confidence(
    history_available: bool,
    medical_history: Optional[List[str]],
    symptoms: List[str],
    chief_complaint: str,
    heart_rate: Optional[float],
    systolic_bp: Optional[float],
    diastolic_bp: Optional[float],
    spo2: Optional[float],
    temperature: Optional[float],
    respiratory_rate: Optional[float],
) -> ConfidenceResult:
    """Calculate confidence score based on data completeness."""
    limitations = []
    score = 1.0

    # --- Vital completeness (40% of confidence) ---
    vital_fields = [heart_rate, systolic_bp, diastolic_bp, spo2, temperature, respiratory_rate]
    vital_present = sum(1 for v in vital_fields if v is not None)
    vital_completeness = vital_present / len(vital_fields)
    vital_contribution = vital_completeness * 0.40

    if vital_present < 3:
        limitations.append("Fewer than 3 vital signs recorded — assessment reliability significantly reduced")
    elif vital_present < 5:
        limitations.append("Incomplete vital signs — some key indicators unavailable")

    if spo2 is None:
        limitations.append("SpO2 not recorded — oxygen saturation risk cannot be assessed")
    if systolic_bp is None:
        limitations.append("Blood pressure not recorded — hemodynamic status uncertain")
    if respiratory_rate is None:
        limitations.append("Respiratory rate not recorded — respiratory distress cannot be fully evaluated")

    # --- History completeness (30% of confidence) ---
    if not history_available:
        history_contribution = 0.10  # Very low if history unavailable
        limitations.append("Medical history unavailable — comorbidities and risk factors unknown")
    elif not medical_history:
        history_contribution = 0.20  # History available but empty — patient has no notable history
        limitations.append("No significant medical history reported")
    else:
        history_contribution = 0.30

    # --- Symptom completeness (20% of confidence) ---
    if not symptoms:
        symptom_contribution = 0.10
        limitations.append("No specific symptoms reported — chief complaint only")
    elif len(symptoms) < 2:
        symptom_contribution = 0.15
    else:
        symptom_contribution = 0.20

    # --- Complaint clarity (10% of confidence) ---
    ambiguous_complaints = {"not feeling well", "feeling unwell", "general malaise", "weakness", "fatigue"}
    if chief_complaint.lower() in ambiguous_complaints or len(chief_complaint) < 5:
        complaint_contribution = 0.03
        limitations.append("Chief complaint is non-specific — underlying cause unclear")
    else:
        complaint_contribution = 0.10

    confidence = vital_contribution + history_contribution + symptom_contribution + complaint_contribution
    confidence = max(0.20, min(1.0, confidence))  # Floor at 0.20, cap at 1.0

    # Data quality
    data_quality = (vital_completeness * 0.5) + (0.3 if history_available else 0.05) + (0.2 if symptoms else 0.05)
    data_quality = min(1.0, data_quality)

    if confidence >= 0.75:
        level = ConfidenceLevel.HIGH
    elif confidence >= 0.50:
        level = ConfidenceLevel.MODERATE
    else:
        level = ConfidenceLevel.LOW

    return ConfidenceResult(
        confidence=round(confidence, 2),
        confidence_level=level,
        limitations=limitations,
        data_quality=round(data_quality, 2)
    )
