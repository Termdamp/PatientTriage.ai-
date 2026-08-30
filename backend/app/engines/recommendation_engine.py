"""
Recommendation Engine - Suggests bed allocations and clinician reallocations.

Identifies potential clinical step-down candidates to resolve bed shortages.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.bed import Bed
from app.models.assessment import Assessment
from app.utils.enums import PatientStatus, Priority
from sqlalchemy import func

def get_allocation_recommendations(db: Session) -> List[Dict[str, Any]]:
    """
    Generate resource and bed reallocation suggestions.
    Returns a list of recommendation dicts:
      - type: 'STEP_DOWN' or 'ADMIT'
      - message: Description of suggestion
      - priority: 'HIGH', 'MEDIUM', 'LOW'
      - metadata: Payload for execution
    """
    recommendations = []

    # 1. Fetch available beds
    beds = db.query(Bed).all()
    gen_avail = [b for b in beds if b.type == "GENERAL" and b.status == "AVAILABLE"]
    crit_avail = [b for b in beds if b.type == "CRITICAL_CARE" and b.status == "AVAILABLE"]

    # 2. Fetch waiting patients (in priority order)
    # Wait, we need to sort active waiting patients by priority: CRITICAL > HIGH > MODERATE > LOW
    # Let's get active patients with status WAITING
    waiting_patients = db.query(Patient).filter(Patient.status == PatientStatus.WAITING).all()

    # Sort waiting patients by priority order (highest first)
    priority_map = {Priority.CRITICAL: 4, Priority.HIGH: 3, Priority.MODERATE: 2, Priority.LOW: 1}
    
    def get_patient_priority_score(p: Patient) -> int:
        if not p.assessments:
            return 0
        latest_ass = sorted(p.assessments, key=lambda a: a.created_at, reverse=True)[0]
        return priority_map.get(latest_ass.priority, 0)

    waiting_patients = sorted(waiting_patients, key=get_patient_priority_score, reverse=True)

    # Count how many critical care patients are waiting
    crit_waiting = []
    other_waiting = []
    for p in waiting_patients:
        if p.assessments:
            latest = sorted(p.assessments, key=lambda a: a.created_at, reverse=True)[0]
            if latest.priority == Priority.CRITICAL:
                crit_waiting.append(p)
            else:
                other_waiting.append(p)
        else:
            other_waiting.append(p)

    # Case A: Critical patient waiting, but no critical care beds are available
    if crit_waiting and not crit_avail:
        # Look for step-down candidates in critical care beds
        # A step-down candidate is a patient in a CRITICAL_CARE bed whose current priority is MODERATE or LOW,
        # and who has a low risk score.
        occupied_crit_beds = [b for b in beds if b.type == "CRITICAL_CARE" and b.status == "OCCUPIED" and b.patient_id is not None]
        
        candidates = []
        for cb in occupied_crit_beds:
            patient = db.query(Patient).filter(Patient.id == cb.patient_id).first()
            if patient and patient.assessments:
                latest = sorted(patient.assessments, key=lambda a: a.created_at, reverse=True)[0]
                if latest.priority in [Priority.MODERATE, Priority.LOW]:
                    # Also check that they aren't marked as deteriorating
                    if not latest.deteriorating:
                        candidates.append((patient, latest, cb))

        # Sort candidates by risk score ascending (safest first)
        candidates = sorted(candidates, key=lambda c: c[1].risk_score)

        if candidates:
            # We have step-down candidates!
            candidate_pat, candidate_ass, bed = candidates[0]
            # Check if there is a general bed available to transfer them to
            if gen_avail:
                target_bed = gen_avail[0]
                incoming_pat = crit_waiting[0]
                recommendations.append({
                    "type": "STEP_DOWN",
                    "priority": "HIGH",
                    "message": f"Critical Care Bed Shortage: Step down {candidate_pat.name} (Stable, Risk {candidate_ass.risk_score:.0f}) from {bed.id} to General Bed {target_bed.id}. This frees up {bed.id} for incoming Critical Patient {incoming_pat.name}.",
                    "metadata": {
                        "stepDownPatientId": candidate_pat.id,
                        "currentBedId": bed.id,
                        "newGeneralBedId": target_bed.id,
                        "incomingPatientId": incoming_pat.id
                    }
                })
            else:
                # No general bed available, maybe transfer to lobby/discharge
                incoming_pat = crit_waiting[0]
                recommendations.append({
                    "type": "STEP_DOWN",
                    "priority": "HIGH",
                    "message": f"Critical Care Bed Shortage: Recommend discharging or moving {candidate_pat.name} (Stable) from {bed.id} to clear bed for incoming Critical Patient {incoming_pat.name}.",
                    "metadata": {
                        "stepDownPatientId": candidate_pat.id,
                        "currentBedId": bed.id,
                        "incomingPatientId": incoming_pat.id
                    }
                })

    # Case B: Standard admissions recommendations
    # Recommend admitting waiting patients to available beds
    for p in waiting_patients:
        # Determine if they need critical care or general bed
        needs_critical = False
        if p.assessments:
            latest = sorted(p.assessments, key=lambda a: a.created_at, reverse=True)[0]
            needs_critical = (latest.priority == Priority.CRITICAL)

        if needs_critical:
            if crit_avail:
                bed = crit_avail.pop(0)
                recommendations.append({
                    "type": "ADMIT",
                    "priority": "HIGH",
                    "message": f"Admit critical patient {p.name} to Critical Care Bed {bed.id}.",
                    "metadata": {
                        "patientId": p.id,
                        "bedId": bed.id
                    }
                })
        else:
            if gen_avail:
                bed = gen_avail.pop(0)
                recommendations.append({
                    "type": "ADMIT",
                    "priority": "MEDIUM" if get_patient_priority_score(p) >= 3 else "LOW",
                    "message": f"Admit patient {p.name} to General Bed {bed.id}.",
                    "metadata": {
                        "patientId": p.id,
                        "bedId": bed.id
                    }
                })

    return recommendations
