"""
Monitoring Service - Periodic checks for reassessment timers and alerts.
"""
import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.alert import Alert
from app.models.assessment import Assessment
from app.utils.enums import PatientStatus, AlertType, AlertSeverity, Priority, EventType
from app.utils.datetime import utcnow
from app.services.alert_service import save_alert
from app.services.audit_service import create_audit_event
from app.realtime.websocket_manager import manager
from app.realtime.events import WebSocketEvent
import uuid

logger = logging.getLogger(__name__)

def check_reassessment_timers(db: Session):
    """
    Scan all active patients (WAITING or IN_REVIEW) and check if their reassessment timers have expired.
    If expired and no active alert exists, create a WAITING_BREACH alert.
    """
    try:
        active_patients = db.query(Patient).filter(
            Patient.status.in_([PatientStatus.WAITING, PatientStatus.IN_REVIEW])
        ).all()
        
        now = utcnow()
        alerts_created = 0

        for patient in active_patients:
            if not patient.next_reassessment_due:
                continue

            # Ensure timezone-aware comparison
            due_time = patient.next_reassessment_due
            if due_time.tzinfo is None:
                due_time = due_time.replace(tzinfo=timezone.utc)

            if due_time < now:
                # Timer breached! Check if an active WAITING_BREACH alert exists
                active_alert = db.query(Alert).filter(
                    Alert.patient_id == patient.id,
                    Alert.type == AlertType.WAITING_BREACH,
                    Alert.acknowledged == False
                ).first()

                if not active_alert:
                    # Fetch latest assessment to find priority
                    latest_ass = db.query(Assessment).filter(
                        Assessment.patient_id == patient.id
                    ).order_by(Assessment.created_at.desc()).first()
                    
                    priority_val = latest_ass.priority if latest_ass else Priority.LOW
                    severity = AlertSeverity.CRITICAL if priority_val == Priority.CRITICAL else AlertSeverity.WARNING
                    
                    message = f"REASSESSMENT OVERDUE: Patient {patient.name} (Triage: {priority_val.value}) is overdue for clinical reassessment (Due at {due_time.strftime('%H:%M:%S')})."
                    
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        patient_id=patient.id,
                        type=AlertType.WAITING_BREACH,
                        severity=severity,
                        message=message,
                        metadata_={"priority": priority_val.value, "dueAt": due_time.isoformat()},
                        acknowledged=False,
                        created_at=utcnow()
                    )
                    db.add(alert)
                    
                    create_audit_event(
                        db, EventType.ALERT_CREATED,
                        f"Triage timer breach alert created for {patient.name}",
                        patient_id=patient.id,
                        metadata={"alertType": "WAITING_BREACH", "priority": priority_val.value}
                    )
                    alerts_created += 1

        if alerts_created > 0:
            db.commit()
            logger.info(f"Reassessment monitor: created {alerts_created} breach alerts.")
            # Trigger WebSocket update to refresh alerts on the dashboard
            return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error in reassessment monitoring task: {e}", exc_info=True)
    return False


async def start_reassessment_monitor(db_session_factory):
    """Async loop to execute reassessment checks periodically."""
    logger.info("Starting background clinical reassessment monitor loop...")
    while True:
        try:
            await asyncio.sleep(20)  # Check every 20 seconds
            db = db_session_factory()
            try:
                alert_fired = check_reassessment_timers(db)
                if alert_fired:
                    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "reassessment_breach"})
            finally:
                db.close()
        except asyncio.CancelledError:
            logger.info("Background reassessment monitor cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
