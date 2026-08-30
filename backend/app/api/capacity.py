from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.bed import Bed
from app.models.patient import Patient
from app.models.resource import ResourceConfiguration
from app.utils.enums import PatientStatus, EventType
from app.services.capacity_service import get_capacity_status
from app.services.audit_service import create_audit_event
from app.realtime.websocket_manager import manager
from app.realtime.events import WebSocketEvent
from app.engines.recommendation_engine import get_allocation_recommendations
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/capacity", tags=["capacity"])

class ResourceConfigUpdate(BaseModel):
    doctorsTotal: Optional[int] = None
    doctorsActive: Optional[int] = None
    nursesTotal: Optional[int] = None
    nursesActive: Optional[int] = None
    ventilatorsTotal: Optional[int] = None
    ventilatorsActive: Optional[int] = None
    monitorsTotal: Optional[int] = None
    monitorsActive: Optional[int] = None

class AllocateBedRequest(BaseModel):
    patientId: str
    bedId: str

class ReleaseBedRequest(BaseModel):
    bedId: str
    patientStatus: Optional[str] = "COMPLETED"  # or WAITING

class ReallocateBedRequest(BaseModel):
    stepDownPatientId: str
    currentBedId: str
    newGeneralBedId: str
    incomingPatientId: str

class AddBedRequest(BaseModel):
    type: str = "GENERAL"  # GENERAL or CRITICAL_CARE
    count: Optional[int] = 1

class BedTotalsRequest(BaseModel):
    generalBeds: int
    criticalBeds: int


def _next_bed_id(db: Session, bed_type: str) -> str:
    """Generate the next sequential bed id for a given type, e.g. BED-GEN-41."""
    prefix = "BED-GEN-" if bed_type == "GENERAL" else "BED-ICU-"
    existing = db.query(Bed).filter(Bed.id.like(f"{prefix}%")).all()
    max_num = 0
    for b in existing:
        try:
            num = int(b.id.replace(prefix, ""))
            max_num = max(max_num, num)
        except ValueError:
            continue
    return f"{prefix}{max_num + 1:02d}"

@router.get("")
def get_capacity(db: Session = Depends(get_db)):
    status = get_capacity_status(db)
    
    # Fetch all individual beds
    beds_list = db.query(Bed).all()
    beds_data = []
    for b in beds_list:
        patient_name = None
        patient_priority = None
        if b.patient_id:
            patient = db.query(Patient).filter(Patient.id == b.patient_id).first()
            if patient:
                patient_name = patient.name
                if patient.assessments:
                    latest = sorted(patient.assessments, key=lambda a: a.created_at, reverse=True)[0]
                    patient_priority = latest.priority.value

        beds_data.append({
            "id": b.id,
            "type": b.type,
            "status": b.status,
            "patientId": b.patient_id,
            "patientName": patient_name,
            "patientPriority": patient_priority
        })

    # Fetch resource configuration
    res = db.query(ResourceConfiguration).first()
    if not res:
        res = ResourceConfiguration()
        db.add(res)
        db.commit()

    resources_data = {
        "doctorsTotal": res.doctors_total,
        "doctorsActive": res.doctors_active,
        "nursesTotal": res.nurses_total,
        "nursesActive": res.nurses_active,
        "ventilatorsTotal": res.ventilators_total,
        "ventilatorsActive": res.ventilators_active,
        "monitorsTotal": res.monitors_total,
        "monitorsActive": res.monitors_active
    }

    # Generate allocation recommendations
    recommendations = get_allocation_recommendations(db)

    # Recalculate utilization numbers
    total_beds_count = len(beds_list)
    occupied_beds_count = sum(1 for b in beds_list if b.status == "OCCUPIED")
    critical_beds_count = sum(1 for b in beds_list if b.type == "CRITICAL_CARE")
    critical_occupied_count = sum(1 for b in beds_list if b.type == "CRITICAL_CARE" and b.status == "OCCUPIED")

    return {
        "totalBeds": total_beds_count,
        "occupiedBeds": occupied_beds_count,
        "availableBeds": total_beds_count - occupied_beds_count,
        "criticalBeds": critical_beds_count,
        "criticalOccupied": critical_occupied_count,
        "criticalAvailable": critical_beds_count - critical_occupied_count,
        "utilization": round(occupied_beds_count / total_beds_count, 2) if total_beds_count else 0,
        "criticalUtilization": round(critical_occupied_count / critical_beds_count, 2) if critical_beds_count else 0,
        "status": "CRITICAL" if (critical_occupied_count >= critical_beds_count or occupied_beds_count / total_beds_count > 0.9) else "WARNING" if (occupied_beds_count / total_beds_count > 0.75) else "NORMAL",
        "warningMessage": "Critical care capacity fully saturated. Recommend clinical step-downs." if critical_occupied_count >= critical_beds_count else None,
        "beds": beds_data,
        "resources": resources_data,
        "recommendations": recommendations
    }

@router.put("/resources")
async def update_resources(payload: ResourceConfigUpdate, db: Session = Depends(get_db)):
    res = db.query(ResourceConfiguration).first()
    if not res:
        res = ResourceConfiguration()
        db.add(res)
    
    if payload.doctorsTotal is not None:
        res.doctors_total = payload.doctorsTotal
    if payload.doctorsActive is not None:
        res.doctors_active = payload.doctorsActive
    if payload.nursesTotal is not None:
        res.nurses_total = payload.nursesTotal
    if payload.nursesActive is not None:
        res.nurses_active = payload.nursesActive
    if payload.ventilatorsTotal is not None:
        res.ventilators_total = payload.ventilatorsTotal
    if payload.ventilatorsActive is not None:
        res.ventilators_active = payload.ventilatorsActive
    if payload.monitorsTotal is not None:
        res.monitors_total = payload.monitorsTotal
    if payload.monitorsActive is not None:
        res.monitors_active = payload.monitorsActive

    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "resource_config_updated"})
    return {"status": "ok", "message": "Resource configuration updated successfully"}

@router.post("/beds/allocate")
async def allocate_bed(req: AllocateBedRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == req.patientId).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    bed = db.query(Bed).filter(Bed.id == req.bedId).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    
    if bed.status == "OCCUPIED" and bed.patient_id != req.patientId:
        raise HTTPException(status_code=400, detail="Bed is already occupied by another patient")

    # If patient is already in another bed, free it
    existing_bed = db.query(Bed).filter(Bed.patient_id == req.patientId).first()
    if existing_bed:
        existing_bed.status = "AVAILABLE"
        existing_bed.patient_id = None

    bed.status = "OCCUPIED"
    bed.patient_id = req.patientId
    patient.status = PatientStatus.IN_TREATMENT
    
    create_audit_event(
        db, EventType.CAPACITY_UPDATED,
        f"Patient {patient.name} assigned to Bed {bed.id}",
        patient_id=patient.id,
        metadata={"bedId": bed.id}
    )
    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "bed_allocated"})
    return {"status": "ok", "message": f"Patient assigned to Bed {bed.id}"}

@router.post("/beds/release")
async def release_bed(req: ReleaseBedRequest, db: Session = Depends(get_db)):
    bed = db.query(Bed).filter(Bed.id == req.bedId).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    
    patient_id = bed.patient_id
    if not patient_id:
        return {"status": "ok", "message": "Bed is already available"}

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    bed.status = "AVAILABLE"
    bed.patient_id = None
    
    if patient:
        patient.status = PatientStatus(req.patientStatus)
        create_audit_event(
            db, EventType.CAPACITY_UPDATED,
            f"Patient {patient.name} released from Bed {bed.id} (Status: {req.patientStatus})",
            patient_id=patient.id,
            metadata={"bedId": bed.id, "finalStatus": req.patientStatus}
        )
    
    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "bed_released"})
    return {"status": "ok", "message": f"Bed {bed.id} released successfully"}

@router.post("/beds/reallocate")
async def reallocate_beds(req: ReallocateBedRequest, db: Session = Depends(get_db)):
    """
    Executes a structured step-down reallocation:
    1. Transfer step-down patient from current critical bed to general bed.
    2. Admit incoming critical patient into the vacated critical bed.
    """
    step_down_patient = db.query(Patient).filter(Patient.id == req.stepDownPatientId).first()
    incoming_patient = db.query(Patient).filter(Patient.id == req.incomingPatientId).first()
    current_bed = db.query(Bed).filter(Bed.id == req.currentBedId).first()
    general_bed = db.query(Bed).filter(Bed.id == req.newGeneralBedId).first()

    if not all([step_down_patient, incoming_patient, current_bed, general_bed]):
        raise HTTPException(status_code=404, detail="One or more patients or beds not found")

    # Step-down patient: move to general bed
    current_bed.patient_id = None
    current_bed.status = "AVAILABLE"

    general_bed.patient_id = step_down_patient.id
    general_bed.status = "OCCUPIED"

    # Incoming patient: move to vacated critical bed
    current_bed.patient_id = incoming_patient.id
    current_bed.status = "OCCUPIED"
    incoming_patient.status = PatientStatus.IN_TREATMENT

    create_audit_event(
        db, EventType.CAPACITY_UPDATED,
        f"REALLOCATION EXECUTED: Step down {step_down_patient.name} to Bed {general_bed.id} to free up Critical Bed {current_bed.id} for incoming Critical Patient {incoming_patient.name}.",
        patient_id=incoming_patient.id,
        metadata={
            "stepDownPatientId": step_down_patient.id,
            "incomingPatientId": incoming_patient.id,
            "criticalBedId": current_bed.id,
            "generalBedId": general_bed.id
        }
    )

    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "bed_reallocated"})
    return {"status": "ok", "message": "Clinical bed reallocation successfully executed"}

@router.post("/beds")
async def add_bed(req: AddBedRequest, db: Session = Depends(get_db)):
    """Add one or more new beds of a given type (GENERAL or CRITICAL_CARE)."""
    bed_type = "CRITICAL_CARE" if req.type == "CRITICAL_CARE" else "GENERAL"
    count = max(1, req.count or 1)
    created_ids = []
    for _ in range(count):
        new_id = _next_bed_id(db, bed_type)
        bed = Bed(id=new_id, type=bed_type, status="AVAILABLE")
        db.add(bed)
        db.flush()
        created_ids.append(new_id)

    create_audit_event(
        db, EventType.CAPACITY_UPDATED,
        f"Added {count} {bed_type} bed(s): {', '.join(created_ids)}",
        metadata={"bedIds": created_ids, "type": bed_type}
    )
    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "bed_added"})
    return {"status": "ok", "message": f"Added {count} bed(s)", "bedIds": created_ids}

@router.delete("/beds/{bed_id}")
async def remove_bed(bed_id: str, db: Session = Depends(get_db)):
    """Remove a bed. Only AVAILABLE (empty) beds can be removed."""
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if bed.status == "OCCUPIED":
        raise HTTPException(status_code=400, detail="Cannot remove an occupied bed. Discharge or transfer the patient first.")

    db.delete(bed)
    create_audit_event(
        db, EventType.CAPACITY_UPDATED,
        f"Removed bed {bed_id}",
        metadata={"bedId": bed_id}
    )
    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "bed_removed"})
    return {"status": "ok", "message": f"Bed {bed_id} removed"}

@router.put("/beds/totals")
async def set_bed_totals(req: BedTotalsRequest, db: Session = Depends(get_db)):
    """
    Reconcile the number of beds of each type to match the requested totals.
    Adds new AVAILABLE beds if increasing; removes AVAILABLE beds (never occupied ones)
    if decreasing. Fails if asked to shrink below the number of currently occupied beds.
    """
    changes = []
    for bed_type, desired in [("GENERAL", req.generalBeds), ("CRITICAL_CARE", req.criticalBeds)]:
        if desired < 0:
            raise HTTPException(status_code=400, detail=f"{bed_type} bed count cannot be negative")

        current_beds = db.query(Bed).filter(Bed.type == bed_type).all()
        current_count = len(current_beds)
        occupied_count = sum(1 for b in current_beds if b.status == "OCCUPIED")

        if desired > current_count:
            to_add = desired - current_count
            for _ in range(to_add):
                new_id = _next_bed_id(db, bed_type)
                db.add(Bed(id=new_id, type=bed_type, status="AVAILABLE"))
                db.flush()
            changes.append(f"+{to_add} {bed_type}")
        elif desired < current_count:
            to_remove = current_count - desired
            if desired < occupied_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot reduce {bed_type} beds below {occupied_count} (currently occupied). Discharge patients first."
                )
            available = [b for b in current_beds if b.status == "AVAILABLE"][:to_remove]
            for b in available:
                db.delete(b)
            changes.append(f"-{to_remove} {bed_type}")

    create_audit_event(
        db, EventType.CAPACITY_UPDATED,
        f"Bed totals updated: {', '.join(changes) if changes else 'no change'}",
        metadata={"generalBeds": req.generalBeds, "criticalBeds": req.criticalBeds}
    )
    db.commit()
    await manager.broadcast(WebSocketEvent.QUEUE_UPDATED, {"reason": "bed_totals_updated"})
    return {"status": "ok", "message": "Bed totals updated" if changes else "No change needed"}
