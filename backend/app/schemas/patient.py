from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.utils.enums import PatientStatus

class PatientCreate(BaseModel):
    name: str
    age: int = Field(..., ge=0, le=150)
    gender: str
    chiefComplaint: str
    symptoms: List[str] = []
    medicalHistory: Optional[List[str]] = None
    historyAvailable: bool = True

class PatientResponse(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    chiefComplaint: str
    symptoms: List[str]
    medicalHistory: Optional[List[str]]
    historyAvailable: bool
    arrivalTime: datetime
    status: PatientStatus
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}

class PatientListItem(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    chiefComplaint: str
    status: PatientStatus
    arrivalTime: datetime

    model_config = {"from_attributes": True}
