from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AuditEventResponse(BaseModel):
    id: str
    patientId: Optional[str]
    eventType: str
    actor: str
    description: str
    metadata: Optional[dict]
    createdAt: datetime

    model_config = {"from_attributes": True}

class AuditListResponse(BaseModel):
    events: List[AuditEventResponse]
    totalCount: int
