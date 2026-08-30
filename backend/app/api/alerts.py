from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.alert_service import get_alerts, acknowledge_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("")
def list_alerts(unacknowledged_only: bool = False, db: Session = Depends(get_db)):
    alerts = get_alerts(db, unacknowledged_only=unacknowledged_only)
    alert_list = [{
        "id": a.id, "patientId": a.patient_id, "type": a.type.value,
        "severity": a.severity.value, "message": a.message,
        "metadata": a.metadata_, "acknowledged": a.acknowledged,
        "createdAt": a.created_at, "resolvedAt": a.resolved_at
    } for a in alerts]
    return {
        "alerts": alert_list,
        "totalCount": len(alert_list),
        "unacknowledgedCount": sum(1 for a in alerts if not a.acknowledged)
    }

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert_endpoint(alert_id: str, db: Session = Depends(get_db)):
    alert = acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.commit()
    return {"id": alert.id, "acknowledged": True, "resolvedAt": alert.resolved_at}
