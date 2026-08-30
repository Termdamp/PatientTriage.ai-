"""
Decision Engine - Combines Risk, Safety, and Confidence into final recommendation.

This does NOT diagnose the patient.
It produces priority and action recommendation for clinician review.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from app.utils.enums import Priority, RecommendedAction
from app.engines.safety_engine import SafetyResult
from app.engines.risk_engine import RiskResult
from app.engines.confidence_engine import ConfidenceResult

PRIORITY_ORDER = {Priority.CRITICAL: 4, Priority.HIGH: 3, Priority.MODERATE: 2, Priority.LOW: 1}

def max_priority(p1: Optional[Priority], p2: Optional[Priority]) -> Optional[Priority]:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    return p1 if PRIORITY_ORDER[p1] >= PRIORITY_ORDER[p2] else p2

@dataclass
class ReasonItem:
    code: str
    message: str

@dataclass
class DecisionResult:
    priority: Priority
    risk_score: float
    safety_floor: Optional[Priority]
    confidence: float
    recommended_action: RecommendedAction
    reasons: List[ReasonItem]
    model_version: str

def priority_to_action(priority: Priority, confidence: float) -> RecommendedAction:
    """Map priority and confidence to recommended action."""
    if priority == Priority.CRITICAL:
        return RecommendedAction.IMMEDIATE_CLINICIAN_REASSESSMENT
    elif priority == Priority.HIGH:
        if confidence < 0.5:
            return RecommendedAction.IMMEDIATE_CLINICIAN_REASSESSMENT  # Low confidence + high risk = escalate
        return RecommendedAction.URGENT_CLINICIAN_REVIEW
    elif priority == Priority.MODERATE:
        return RecommendedAction.CLINICIAN_REVIEW
    else:
        return RecommendedAction.ROUTINE_REVIEW

def make_decision(
    risk_result: RiskResult,
    safety_result: SafetyResult,
    confidence_result: ConfidenceResult,
) -> DecisionResult:
    """Combine risk, safety, and confidence into final decision."""
    reasons: List[ReasonItem] = []

    # 1. Start with risk-based priority
    risk_priority = risk_result.priority

    # 2. Apply safety floor (safety can only raise, never lower priority)
    final_priority = max_priority(risk_priority, safety_result.safety_floor)

    # 3. Generate reasons from risk factors
    for factor in risk_result.factors[:5]:  # Top 5 factors
        code = factor.name.upper().replace(" ", "_")
        reasons.append(ReasonItem(code=code, message=factor.description))

    # 4. Add safety-specific reasons
    for flag in safety_result.flags[:5]:
        reasons.append(ReasonItem(
            code=flag,
            message=f"Safety flag triggered: {flag.replace('_', ' ').title()}"
        ))

    # 5. If safety floor raised priority, explain why
    if safety_result.safety_floor and PRIORITY_ORDER.get(safety_result.safety_floor, 0) > PRIORITY_ORDER.get(risk_priority, 0):
        reasons.append(ReasonItem(
            code="SAFETY_FLOOR_APPLIED",
            message=f"Safety evaluation raised priority from {risk_priority.value} to {safety_result.safety_floor.value}"
        ))

    # 6. Confidence limitations
    if confidence_result.confidence < 0.5:
        reasons.append(ReasonItem(
            code="LOW_CONFIDENCE_ASSESSMENT",
            message="Assessment confidence is limited due to incomplete data — err on the side of caution"
        ))

    # 7. Recommended action
    recommended_action = priority_to_action(final_priority, confidence_result.confidence)

    return DecisionResult(
        priority=final_priority,
        risk_score=risk_result.risk_score,
        safety_floor=safety_result.safety_floor,
        confidence=confidence_result.confidence,
        recommended_action=recommended_action,
        reasons=reasons,
        model_version="prototype-rules-v1"
    )
