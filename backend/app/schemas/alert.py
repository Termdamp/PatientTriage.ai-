from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.utils.enums import AlertType, AlertSeverity

class AlertResponse(BaseModel):
    id: str
    patientId: Optional[str]
    type: AlertType
    severity: AlertSeverity
    message: str
    metadata: Optional[dict]
    acknowledged: bool
    createdAt: datetime
    resolvedAt: Optional[datetime]

    model_config = {"from_attributes": True}

class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    totalCount: int
    unacknowledgedCount: int
