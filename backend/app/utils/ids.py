import uuid

def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    uid = str(uuid.uuid4()).replace("-", "")[:12].upper()
    if prefix:
        return f"{prefix}{uid}"
    return uid

def patient_id() -> str:
    return generate_id("P")

def assessment_id() -> str:
    return generate_id("A")

def alert_id() -> str:
    return generate_id("AL")

def override_id() -> str:
    return generate_id("OV")

def audit_id() -> str:
    return generate_id("AU")
