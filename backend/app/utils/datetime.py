from datetime import datetime, timezone

def utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)

def minutes_since(dt: datetime) -> float:
    """Calculate minutes elapsed since a given datetime."""
    now = utcnow()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    return delta.total_seconds() / 60
