"""Creation identity is immutable, even when a task later receives results."""
from __future__ import annotations

import hashlib
import json

from app.db.models import Task
from app.domain.schemas import TaskCreate


def canonical_json_hash(payload: object) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def creation_body(payload: TaskCreate) -> dict[str, object]:
    body = payload.model_dump(mode="json")
    # Before categories existed the field was absent from the stored hash.
    if body.get("category") is None:
        body.pop("category", None)
    return body


def new_task(payload: TaskCreate, key: str | None = None) -> Task:
    body = creation_body(payload)
    return Task(**body, status="pending", create_idempotency_key=key,
                create_request_hash=canonical_json_hash(body))
