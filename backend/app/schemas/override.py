from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.utils.enums import Priority

class OverrideRequest(BaseModel):
    patientId: str
    assessmentId: str
    newPriority: Priority
    reason: str = Field(..., min_length=5)
    clinicianId: str

class OverrideResponse(BaseModel):
    id: str
    patientId: str
    assessmentId: str
    originalPriority: Priority
    newPriority: Priority
    reason: str
    clinicianId: str
    createdAt: datetime

    model_config = {"from_attributes": True}
