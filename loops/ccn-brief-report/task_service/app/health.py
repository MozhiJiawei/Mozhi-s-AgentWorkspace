from __future__ import annotations

from redis import Redis
from sqlalchemy import text

from app.config import get_settings
from app.db.session import SessionLocal


def main() -> int:
    settings = get_settings()
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    client = Redis.from_url(settings.redis_url, socket_timeout=2)
    if not client.ping():
        raise RuntimeError("Redis did not answer PING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
