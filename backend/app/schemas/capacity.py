from pydantic import BaseModel
from datetime import datetime

class CapacityResponse(BaseModel):
    totalBeds: int
    occupiedBeds: int
    availableBeds: int
    criticalBeds: int
    criticalOccupied: int
    criticalAvailable: int
    utilization: float
    criticalUtilization: float
    status: str  # NORMAL, WARNING, CRITICAL
    updatedAt: datetime
