"""
Alert Engine - Generates alerts for critical conditions.

Alerts are generated for:
- Critical safety events
- Patient deterioration
- Waiting time breaches
- Capacity concerns
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from app.utils.enums import AlertType, AlertSeverity, Priority

@dataclass
class AlertCandidate:
    type: AlertType
    severity: AlertSeverity
    patient_id: Optional[str]
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

def generate_triage_alerts(
    patient_id: str,
    patient_name: str,
    priority: Priority,
    safety_flags: List[str],
    deteriorating: bool = False,
    previous_priority: Optional[Priority] = None,
) -> List[AlertCandidate]:
    """Generate alerts after a triage assessment."""
    alerts: List[AlertCandidate] = []

    # Critical safety event alert
    if priority == Priority.CRITICAL and safety_flags:
        alerts.append(AlertCandidate(
            type=AlertType.DETERIORATION if deteriorating else AlertType.SYSTEM,
            severity=AlertSeverity.CRITICAL,
            patient_id=patient_id,
            message=f"CRITICAL: {patient_name} has critical safety flags: {', '.join(safety_flags[:3])}",
            metadata={"flags": safety_flags, "priority": priority.value}
        ))

    # Deterioration alert
    if deteriorating:
        previous = previous_priority.value if previous_priority else "UNKNOWN"
        alerts.append(AlertCandidate(
            type=AlertType.DETERIORATION,
            severity=AlertSeverity.CRITICAL if priority == Priority.CRITICAL else AlertSeverity.WARNING,
            patient_id=patient_id,
            message=f"DETERIORATION DETECTED: {patient_name} has deteriorated (Priority: {previous} → {priority.value})",
            metadata={"previousPriority": previous, "newPriority": priority.value}
        ))

    return alerts

def generate_waiting_breach_alert(
    patient_id: str,
    patient_name: str,
    priority: Priority,
    wait_minutes: float,
    threshold_minutes: int
) -> AlertCandidate:
    """Generate alert for waiting time breach."""
    return AlertCandidate(
        type=AlertType.WAITING_BREACH,
        severity=AlertSeverity.WARNING if priority != Priority.CRITICAL else AlertSeverity.CRITICAL,
        patient_id=patient_id,
        message=f"WAITING BREACH: {patient_name} ({priority.value}) has waited {wait_minutes:.0f} minutes (threshold: {threshold_minutes}min)",
        metadata={"waitMinutes": wait_minutes, "thresholdMinutes": threshold_minutes, "priority": priority.value}
    )

def generate_capacity_alert(utilization: float, critical_utilization: float) -> AlertCandidate:
    """Generate capacity warning alert."""
    severity = AlertSeverity.CRITICAL if critical_utilization > 0.95 else AlertSeverity.WARNING
    return AlertCandidate(
        type=AlertType.CAPACITY,
        severity=severity,
        patient_id=None,
        message=f"CAPACITY: ED at {utilization*100:.0f}% capacity. Critical beds at {critical_utilization*100:.0f}%.",
        metadata={"utilization": utilization, "criticalUtilization": critical_utilization}
    )
