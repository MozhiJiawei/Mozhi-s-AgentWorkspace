"""Date boundaries and keyset pagination for the dashboard's updated-time order."""
import base64
import binascii
import json
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException

BEIJING = timezone(timedelta(hours=8))


def day_boundary(value: date, *, exclusive_end: bool = False) -> datetime:
    try:
        day = value + timedelta(days=1) if exclusive_end else value
        return datetime.combine(day, time.min, BEIJING).astimezone(timezone.utc)
    except OverflowError as exc:
        raise HTTPException(422, {"code": "invalid_date_range", "message": "Date out of range"}) from exc


def updated_token(timestamp: datetime, row_number: int) -> str:
    stamp = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
    raw = json.dumps([stamp.isoformat(), row_number], separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def parse_updated_token(token: str) -> tuple[datetime, int]:
    try:
        raw = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
        timestamp, row_number = json.loads(raw)
        stamp = datetime.fromisoformat(timestamp)
        if stamp.tzinfo is None or type(row_number) is not int or not 1 <= row_number <= 2**63 - 1:
            raise ValueError("Invalid cursor")
        return stamp.astimezone(timezone.utc), row_number
    except (ValueError, TypeError, OverflowError, binascii.Error, UnicodeError) as exc:
        raise HTTPException(422, {"code": "invalid_page_token", "message": "Invalid updated-time cursor"}) from exc
