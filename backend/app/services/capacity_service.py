import logging
from sqlalchemy.orm import Session
from app.models.capacity import Capacity
from app.engines.capacity_engine import evaluate_capacity, CapacityStatus
from app.utils.datetime import utcnow
import uuid

logger = logging.getLogger(__name__)

def get_capacity_record(db: Session) -> Capacity:
    """Get or create the single capacity record."""
    capacity = db.query(Capacity).first()
    if not capacity:
        capacity = Capacity(
            id=str(uuid.uuid4()),
            total_beds=50,
            occupied_beds=25,
            critical_beds=10,
            critical_occupied=5,
            updated_at=utcnow()
        )
        db.add(capacity)
        db.flush()
    return capacity

def get_capacity_status(db: Session) -> CapacityStatus:
    """Get current capacity status."""
    capacity = get_capacity_record(db)
    return evaluate_capacity(
        total_beds=capacity.total_beds,
        occupied_beds=capacity.occupied_beds,
        critical_beds=capacity.critical_beds,
        critical_occupied=capacity.critical_occupied,
    )

def update_capacity(
    db: Session,
    occupied_beds: int = None,
    critical_occupied: int = None
) -> CapacityStatus:
    capacity = get_capacity_record(db)
    if occupied_beds is not None:
        capacity.occupied_beds = min(occupied_beds, capacity.total_beds)
    if critical_occupied is not None:
        capacity.critical_occupied = min(critical_occupied, capacity.critical_beds)
    capacity.updated_at = utcnow()
    db.flush()
    return evaluate_capacity(
        capacity.total_beds, capacity.occupied_beds,
        capacity.critical_beds, capacity.critical_occupied
    )
