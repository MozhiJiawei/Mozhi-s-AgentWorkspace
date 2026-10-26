"""Beijing date boundaries for task-list filters."""
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException

BEIJING = timezone(timedelta(hours=8))


def day_boundary(value: date, *, exclusive_end: bool = False) -> datetime:
    try:
        day = value + timedelta(days=1) if exclusive_end else value
        return datetime.combine(day, time.min, BEIJING).astimezone(timezone.utc)
    except OverflowError as exc:
        raise HTTPException(422, {"code": "invalid_date_range", "message": "Date out of range"}) from exc
