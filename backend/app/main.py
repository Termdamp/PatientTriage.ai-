import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import check_database_connection
from app.realtime.websocket_manager import manager
from app.api import patients, triage, queue, alerts, capacity, simulation, override, audit

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("DISCLAIMER: This is a prototype using synthetic data. Not for clinical use.")
    db_ok = check_database_connection()
    monitor_task = None
    if db_ok:
        logger.info("Database connection: OK")
        _auto_seed_if_empty()
        # Start background reassessment monitor
        from app.services.monitoring_service import start_reassessment_monitor
        from app.core.database import SessionLocal
        monitor_task = asyncio.create_task(start_reassessment_monitor(SessionLocal))
    else:
        logger.warning("Database connection: FAILED — some features will not work")
    yield
    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutting down PatientTriage.ai backend")


def _auto_seed_if_empty():
    """Create tables and load synthetic demo patients if the DB is empty.

    This makes the app self-sufficient on hosts with ephemeral disks
    (e.g. Render's free tier with SQLite): every fresh boot re-seeds
    automatically instead of requiring a manual script run.
    """
    from app.core.database import SessionLocal, Base, engine
    from app.models.patient import Patient
    try:
        # Ensure tables exist before checking/seeding (safe if already created).
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            has_patients = db.query(Patient).first() is not None
        finally:
            db.close()
        if not has_patients:
            logger.info("No patients found — auto-seeding synthetic demo data...")
            from scripts.seed_database import seed
            seed()
            logger.info("Auto-seed complete.")
        else:
            logger.info("Existing patient data found — skipping auto-seed.")
    except Exception as e:
        logger.error(f"Auto-seed check failed: {e}")

app = FastAPI(
    title="PatientTriage.ai API",
    description="AI-assisted patient triage decision support. PROTOTYPE — Synthetic data only. NOT for clinical use.",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(patients.router)
app.include_router(triage.router)
app.include_router(queue.router)
app.include_router(alerts.router)
app.include_router(capacity.router)
app.include_router(simulation.router)
app.include_router(override.router)
app.include_router(audit.router)

@app.get("/health", tags=["system"])
def health_check():
    db_connected = check_database_connection()
    return {
        "status": "ok" if db_connected else "degraded",
        "database": "connected" if db_connected else "disconnected",
        "version": settings.APP_VERSION,
        "disclaimer": "Prototype. Synthetic data. Not for clinical use."
    }

@app.websocket("/ws/queue")
async def websocket_queue(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_personal(websocket, {
            "event": "CONNECTED",
            "message": "Connected to PatientTriage.ai real-time queue"
        })
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
