from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.service import Principal, require_api_key
from app.db.models import BatchCreation, Task
from app.db.session import get_db
from app.domain.schemas import TaskBatchCreate, TaskBatchResponse
from app.domain.task_creation import canonical_json_hash, creation_body, new_task

router = APIRouter()


@router.post("/api/v1/tasks/batch", response_model=TaskBatchResponse, status_code=201,
             responses={200: {"model": TaskBatchResponse}, 409: {"description": "Creation conflict"},
                        413: {"description": "Request exceeds 10 MiB"}})
def create_tasks(
    payload: TaskBatchCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    _principal: Principal = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> JSONResponse:
    bodies = [creation_body(item) for item in payload.tasks]
    request_hash = canonical_json_hash({"tasks": bodies})
    ids = [item.task_id for item in payload.tasks]
    request.state.batch_counts = {"requested": len(ids)}
    for _attempt in range(3):
        if idempotency_key:
            saved = db.get(BatchCreation, idempotency_key)
            if saved:
                if saved.request_hash != request_hash:
                    raise HTTPException(409, {"code": "idempotency_conflict", "message": "Idempotency-Key was reused"})
                request.state.batch_counts = {key: saved.response_body["data"][key]
                                             for key in ("requested", "created", "existing")}
                return JSONResponse(saved.response_body, status_code=saved.status_code)
        existing = {task.task_id: task for task in db.scalars(select(Task).where(Task.task_id.in_(ids)))}
        conflicts = [{"index": index, "task_id": item.task_id}
                     for index, item in enumerate(payload.tasks)
                     if item.task_id in existing and existing[item.task_id].create_request_hash != canonical_json_hash(bodies[index])]
        if conflicts:
            raise HTTPException(409, {"code": "task_conflict", "message": "Existing tasks have different creation data", "details": conflicts})
        items = [{"index": index, "task_id": item.task_id,
                  "disposition": "existing" if item.task_id in existing else "created"}
                 for index, item in enumerate(payload.tasks)]
        counts = {"requested": len(ids), "created": len(ids) - len(existing), "existing": len(existing)}
        body = {"status": "success", "data": {**counts, "items": items}}
        code = 201 if counts["created"] else 200
        # Stable lock acquisition order prevents reversed overlapping batches
        # from deadlocking on the task_id unique index.
        db.add_all(new_task(item) for item in sorted(payload.tasks, key=lambda item: item.task_id)
                   if item.task_id not in existing)
        if idempotency_key:
            db.add(BatchCreation(key=idempotency_key, request_hash=request_hash, response_body=body, status_code=code))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        request.state.batch_counts = counts
        return JSONResponse(body, status_code=code)
    raise HTTPException(409, {"code": "concurrent_creation", "message": "Concurrent creation; retry the same request"}, headers={"Retry-After": "1"})
