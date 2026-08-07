from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))
os.environ.update(
    {
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "REDIS_URL": "redis://unused:6379/0",
        "CCN_API_KEY": "single-test-key",
    }
)

from app.db.models import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.rate_limit.service import get_rate_limiter  # noqa: E402


class FakeLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int]] = []

    def check(self, bucket: str, identifier: str, limit: int) -> None:
        self.calls.append((bucket, identifier, limit))


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    limiter = FakeLimiter()

    def override_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    with TestClient(app) as test_client:
        test_client.fake_limiter = limiter
        test_client.db_factory = factory
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def api_headers() -> dict[str, str]:
    return {"Authorization": "Bearer single-test-key"}


@pytest.fixture
def sample_task() -> dict[str, str]:
    return {
        "task_id": "TASK-20260804-01",
        "content": "验证统一任务接口",
        "url": "https://example.test/source",
        "hotspot_id": "HS-1",
        "period": "2026-W32",
    }
