import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.engines.alert_engine import AlertCandidate
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)

def save_alert(db: Session, candidate: AlertCandidate) -> Alert:
    alert = Alert(
        id=str(uuid.uuid4()),
        patient_id=candidate.patient_id,
        type=candidate.type,
        severity=candidate.severity,
        message=candidate.message,
        metadata_=candidate.metadata,
        acknowledged=False,
        created_at=utcnow()
    )
    db.add(alert)
    db.flush()
    logger.info(f"Alert saved: {alert.type} - {alert.message[:60]}")
    return alert

def get_alerts(db: Session, unacknowledged_only: bool = False, limit: int = 50) -> List[Alert]:
    query = db.query(Alert)
    if unacknowledged_only:
        query = query.filter(Alert.acknowledged == False)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()

def acknowledge_alert(db: Session, alert_id: str) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.acknowledged = True
        alert.resolved_at = utcnow()
        db.flush()
    return alert
