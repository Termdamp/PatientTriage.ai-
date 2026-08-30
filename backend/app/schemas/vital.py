from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VitalInput(BaseModel):
    heartRate: Optional[float] = Field(None, ge=0, le=300)
    systolicBp: Optional[float] = Field(None, ge=0, le=300)
    diastolicBp: Optional[float] = Field(None, ge=0, le=200)
    spo2: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=30, le=45)
    respiratoryRate: Optional[float] = Field(None, ge=0, le=100)

class VitalResponse(BaseModel):
    id: str
    patientId: str
    heartRate: Optional[float]
    systolicBp: Optional[float]
    diastolicBp: Optional[float]
    spo2: Optional[float]
    temperature: Optional[float]
    respiratoryRate: Optional[float]
    timestamp: datetime

    model_config = {"from_attributes": True}
