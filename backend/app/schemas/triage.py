from pydantic import BaseModel, Field
from typing import Optional, List
from app.utils.enums import Priority, RecommendedAction, AgeGroup, ConfidenceLevel
from app.schemas.vital import VitalInput

class ReasonItem(BaseModel):
    code: str
    message: str

class TriageRequest(BaseModel):
    patientId: Optional[str] = None  # If provided, update existing patient
    name: Optional[str] = None
    age: int = Field(..., ge=0, le=150)
    gender: str
    chiefComplaint: str
    symptoms: List[str] = []
    historyAvailable: bool = True
    medicalHistory: Optional[List[str]] = None
    vitals: VitalInput

class TriageResponse(BaseModel):
    patientId: str
    priority: Priority
    riskScore: float
    confidence: float
    confidenceLevel: ConfidenceLevel
    safetyFloor: Optional[Priority]
    safetyFlags: List[str]
    reasons: List[ReasonItem]
    recommendedAction: RecommendedAction
    ageGroup: AgeGroup
    dataQuality: float
    limitations: List[str]
    modelVersion: str
    deteriorating: bool
    deteriorationSeverity: Optional[str]
    explanation: Optional[str] = None
