"""
Reset database and re-seed with fresh demo data.

Run: python scripts/reset_database.py

WARNING: This deletes ALL data and re-seeds from scratch.
Use before a demo to ensure a clean, known state.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import engine, Base, SessionLocal
from app.models.patient import Patient
from app.models.vital import Vital
from app.models.assessment import Assessment
from app.models.alert import Alert
from app.models.override import Override
from app.models.audit import AuditEvent
from app.models.capacity import Capacity
from app.models.bed import Bed
from app.models.resource import ResourceConfiguration

def reset():
    print("Resetting database...")
    print("WARNING: All data will be deleted.")

    db = SessionLocal()
    try:
        # Delete in correct order (respecting relationships)
        db.query(AuditEvent).delete()
        db.query(Override).delete()
        db.query(Alert).delete()
        db.query(Assessment).delete()
        db.query(Vital).delete()
        db.query(Capacity).delete()
        db.query(Bed).delete()
        db.query(ResourceConfiguration).delete()
        db.query(Patient).delete()
        db.commit()
        print("All data deleted.")
    except Exception as e:
        db.rollback()
        print(f"Error during reset: {e}")
        raise
    finally:
        db.close()

    # Re-seed
    print("Re-seeding...")
    from scripts.seed_database import seed
    seed()
    print("\nDatabase reset complete. Demo is ready.")

if __name__ == '__main__':
    reset()
