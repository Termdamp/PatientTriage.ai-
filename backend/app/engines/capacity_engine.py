"""
Capacity Engine - Tracks and evaluates ED bed capacity.

This provides decision support only.
The system does NOT admit, deny, or discharge patients.
"""
from dataclasses import dataclass
from typing import Optional
from app.core.config import settings

@dataclass
class CapacityStatus:
    total_beds: int
    occupied_beds: int
    available_beds: int
    critical_beds: int
    critical_occupied: int
    critical_available: int
    utilization: float
    critical_utilization: float
    status: str  # NORMAL, WARNING, CRITICAL
    warning_message: Optional[str]

def evaluate_capacity(
    total_beds: int,
    occupied_beds: int,
    critical_beds: int,
    critical_occupied: int
) -> CapacityStatus:
    """Evaluate current capacity and return status."""
    available_beds = total_beds - occupied_beds
    critical_available = critical_beds - critical_occupied
    utilization = occupied_beds / total_beds if total_beds > 0 else 0
    critical_utilization = critical_occupied / critical_beds if critical_beds > 0 else 0

    warning_message = None
    if critical_utilization >= 0.95:
        status = "CRITICAL"
        warning_message = f"Critical care capacity severely constrained: {critical_available} bed(s) remaining"
    elif critical_utilization >= settings.CRITICAL_CAPACITY_WARNING_THRESHOLD or utilization >= settings.CAPACITY_WARNING_THRESHOLD:
        status = "WARNING"
        warning_message = f"ED approaching capacity: {available_beds} beds available, {critical_available} critical beds available"
    else:
        status = "NORMAL"

    return CapacityStatus(
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        available_beds=available_beds,
        critical_beds=critical_beds,
        critical_occupied=critical_occupied,
        critical_available=critical_available,
        utilization=round(utilization, 3),
        critical_utilization=round(critical_utilization, 3),
        status=status,
        warning_message=warning_message
    )
