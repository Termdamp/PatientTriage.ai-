from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.utils.enums import Priority, RecommendedAction

class QueueItem(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    chiefComplaint: str
    priority: Priority
    riskScore: float
    confidence: float
    waitMinutes: float
    deteriorating: bool
    safetyFlags: List[str]
    reasons: List[dict]
    recommendedAction: RecommendedAction
    queuePosition: int

class QueueResponse(BaseModel):
    patients: List[QueueItem]
    totalCount: int
    criticalCount: int
    highCount: int
    moderateCount: int
    lowCount: int
    updatedAt: datetime
