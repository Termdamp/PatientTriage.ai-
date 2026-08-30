from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.triage import TriageRequest, TriageResponse
from app.services.triage_service import run_triage
from app.realtime.websocket_manager import manager
from app.realtime.events import WebSocketEvent
import logging

router = APIRouter(prefix="/triage", tags=["triage"])
logger = logging.getLogger(__name__)

@router.post("", response_model=TriageResponse)
async def triage_patient(request: TriageRequest, db: Session = Depends(get_db)):
    try:
        result = run_triage(db, request)
        db.commit()
        # Broadcast to WebSocket clients
        await manager.broadcast(WebSocketEvent.PATIENT_UPDATED, {
            "patientId": result.patientId,
            "priority": result.priority.value,
            "riskScore": result.riskScore,
            "deteriorating": result.deteriorating
        })
        await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "triage_completed"})
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Triage failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Triage processing failed")
