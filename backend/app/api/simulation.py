from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.simulation_service import simulate_deterioration, simulate_surge
from app.realtime.websocket_manager import manager
from app.realtime.events import WebSocketEvent
import logging

router = APIRouter(prefix="/simulate", tags=["simulation"])
logger = logging.getLogger(__name__)

@router.post("/deterioration/{patient_id}")
async def simulate_patient_deterioration(patient_id: str, db: Session = Depends(get_db)):
    try:
        result = simulate_deterioration(db, patient_id)
        triage = result["triageResult"]
        await manager.broadcast(WebSocketEvent.DETERIORATION, {
            "patientId": patient_id,
            "newPriority": triage.priority.value,
            "deteriorating": triage.deteriorating,
            "safetyFlags": triage.safetyFlags
        })
        await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "deterioration"})
        if triage.priority.value == "CRITICAL":
            await manager.broadcast(WebSocketEvent.ALERT_CREATED, {
                "patientId": patient_id,
                "severity": "CRITICAL",
                "message": f"Patient {patient_id} deteriorated to CRITICAL"
            })
        return {
            "patientId": result["patientId"],
            "previousVitals": result["previousVitals"],
            "newVitals": result["newVitals"],
            "newPriority": triage.priority.value,
            "riskScore": triage.riskScore,
            "confidence": triage.confidence,
            "safetyFlags": triage.safetyFlags,
            "reasons": [{"code": r.code, "message": r.message} for r in triage.reasons],
            "deteriorating": triage.deteriorating
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Deterioration simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Simulation failed")

@router.post("/surge")
def trigger_surge(payload: dict, db: Session = Depends(get_db)):
    multiplier = payload.get("multiplier", 1)
    try:
        multiplier = int(multiplier)
        result = simulate_surge(db, multiplier)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
