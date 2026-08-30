"""
Queue Engine - Prioritizes patients for clinician review.

Queue ordering:
1. Priority (CRITICAL > HIGH > MODERATE > LOW)
2. Deterioration status (deteriorating patients moved up)
3. Waiting time (longer wait = higher urgency within same priority)

The queue explains why each patient is in their position.
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from app.utils.enums import Priority
from app.utils.datetime import minutes_since

PRIORITY_SORT = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MODERATE: 2, Priority.LOW: 3}

@dataclass
class QueueEntry:
    patient_id: str
    name: str
    age: int
    gender: str
    chief_complaint: str
    priority: Priority
    risk_score: float
    confidence: float
    arrival_time: datetime
    deteriorating: bool
    safety_flags: List[str]
    reasons: List[dict]
    recommended_action: str
    override_priority: Optional[Priority] = None  # If clinician override exists

    @property
    def effective_priority(self) -> Priority:
        """The priority used for queue ordering (override takes precedence)."""
        return self.override_priority if self.override_priority is not None else self.priority

    @property
    def wait_minutes(self) -> float:
        return minutes_since(self.arrival_time)

def sort_key(entry: QueueEntry):
    """Sort function: priority → deterioration → wait time."""
    priority_val = PRIORITY_SORT[entry.effective_priority]
    # Deteriorating patients sort above stable at same priority
    deterioration_val = 0 if entry.deteriorating else 1
    # Longer wait = higher urgency (negative for ascending sort)
    wait_val = -entry.wait_minutes
    return (priority_val, deterioration_val, wait_val)

def build_queue(entries: List[QueueEntry]) -> List[QueueEntry]:
    """Return sorted queue."""
    return sorted(entries, key=sort_key)
