from __future__ import annotations

from datetime import date
from typing import Literal

from app.domain.task_creation import canonical_json_hash, creation_body, new_task
from app.domain.list_filters import day_boundary, parse_updated_token, updated_token

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth.service import Principal, require_api_key
from app.db.models import Task, TaskResult, utc_now
from app.db.session import get_db
from app.domain.schemas import ResultCreate, ResultView, TaskBatchDelete, TaskCreate, TaskView
from app.domain.urls import normalize_http_iri


router = APIRouter()
STATUS_ALIASES = {
    "pending": "pending",
    "未领取": "pending",
    "completed": "completed",
    "已完成": "completed",
    "failed": "failed",
    "失败": "failed",
}


def normalized_result_payload(payload: ResultCreate) -> dict[str, object]:
    body = payload.model_dump(mode="json")
    body["artifact_urls"] = [normalize_http_iri(item) for item in payload.artifact_urls]
    return body


def stored_result_payload(result: TaskResult) -> dict[str, object]:
    return {
        "outcome": result.outcome,
        "summary": result.summary,
        "artifact_urls": [normalize_http_iri(item) for item in result.artifact_urls],
        "error": result.error,
        "metadata": dict(result.extra_metadata),
    }


def result_view(result: TaskResult) -> ResultView:
    return ResultView(
        attempt=result.attempt,
        outcome=result.outcome,
        summary=result.summary,
        artifact_urls=[normalize_http_iri(item) for item in result.artifact_urls],
        error=result.error,
        metadata=dict(result.extra_metadata),
        created_at=result.created_at,
    )


def task_view(task: Task) -> TaskView:
    latest = task.results[-1] if task.results else None
    return TaskView(
        category=task.category,
        row_number=task.row_number,
        task_id=task.task_id,
        content=task.content,
        url=task.url,
        hotspot_id=task.hotspot_id,
        period=task.period,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        latest_result=result_view(latest) if latest else None,
    )


def task_query():
    return select(Task).options(selectinload(Task.results))


def success(data: object, **extra: object) -> dict[str, object]:
    return {"status": "success", "data": data, **extra}


def contains(column, value: str):
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


@router.post("/api/v1/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    _principal: Principal = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    body = creation_body(payload)
    request_hash = canonical_json_hash(body)
    existing = db.scalar(task_query().where(Task.task_id == payload.task_id))
    if existing:
        if existing.create_request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail={"code": "task_conflict", "message": "task_id already exists with different data"},
            )
        return success(task_view(existing).model_dump(mode="json"))
    if idempotency_key:
        idem = db.scalar(task_query().where(Task.create_idempotency_key == idempotency_key))
        if idem:
            if idem.create_request_hash != request_hash:
                raise HTTPException(
                    status_code=409,
                    detail={"code": "idempotency_conflict", "message": "Idempotency-Key was reused"},
                )
            return success(task_view(idem).model_dump(mode="json"))
    task = new_task(payload, idempotency_key)
    db.add(task)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "task_conflict", "message": "Task or Idempotency-Key already exists"},
        ) from exc
    db.refresh(task)
    task.results = []
    return success(task_view(task).model_dump(mode="json"))


@router.get("/api/v1/tasks/{task_id}")
def get_task(
    task_id: str,
    _principal: Principal = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    task = db.scalar(task_query().where(Task.task_id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "message": "Task not found"})
    return success(task_view(task).model_dump(mode="json"))


@router.delete("/api/v1/tasks/{task_id}")
def delete_task(
    task_id: str,
    _principal: Principal = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    task = db.scalar(task_query().where(Task.task_id == task_id))
    if not task:
        return success({"task_id": task_id, "deleted": False})
    db.delete(task)
    db.commit()
    return success({"task_id": task_id, "deleted": True})


@router.delete("/api/v1/tasks")
def delete_tasks(
    payload: TaskBatchDelete,
    _principal: Principal = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    tasks = list(db.scalars(task_query().where(Task.task_id.in_(payload.task_ids))).unique())
    found = {task.task_id for task in tasks}
    for task in tasks:
        db.delete(task)
    db.commit()
    return success(
        {
            "requested": len(payload.task_ids),
            "deleted": len(tasks),
            "missing": [task_id for task_id in payload.task_ids if task_id not in found],
        }
    )


@router.get("/api/v1/tasks")
def list_tasks(
    task_status: str | None = Query(default=None, alias="status"),
    query_text: str | None = Query(default=None, alias="q", min_length=1, max_length=128),
    hotspot_id: str | None = Query(default=None, min_length=1, max_length=128),
    period: str | None = Query(default=None, min_length=1, max_length=64),
    limit: int = Query(default=100, ge=1, le=500),
    cursor: int | None = Query(default=None, ge=0),
    sort: Literal["row_number", "updated_desc"] = Query(default="row_number"),
    updated_from: date | None = Query(default=None, description="更新时间起始日期，按北京时间包含当天"),
    updated_to: date | None = Query(default=None, description="更新时间结束日期，按北京时间包含当天"),
    page_token: str | None = Query(default=None, min_length=1, max_length=256),
    _principal: Principal = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if updated_from and updated_to and updated_from > updated_to:
        raise HTTPException(422, {"code": "invalid_date_range", "message": "Start date must not exceed end date"})
    if (sort == "updated_desc" and cursor is not None) or (sort == "row_number" and page_token is not None):
        raise HTTPException(422, {"code": "invalid_cursor", "message": "Cursor does not match sort order"})
    query = task_query().limit(limit + 1)
    if sort == "updated_desc":
        query = query.order_by(Task.updated_at.desc(), Task.row_number.desc())
        if page_token:
            stamp, row_number = parse_updated_token(page_token)
            query = query.where(or_(Task.updated_at < stamp,
                                    (Task.updated_at == stamp) & (Task.row_number < row_number)))
    else:
        query = query.order_by(Task.row_number)
    if updated_from:
        query = query.where(Task.updated_at >= day_boundary(updated_from))
    if updated_to:
        query = query.where(Task.updated_at < day_boundary(updated_to, exclusive_end=True))
    if task_status:
        canonical = STATUS_ALIASES.get(task_status)
        if not canonical:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_status", "message": "Unknown task status"},
            )
        query = query.where(Task.status == canonical)
    if query_text:
        query = query.where(
            or_(
                contains(Task.task_id, query_text),
                contains(Task.hotspot_id, query_text),
                contains(Task.period, query_text),
            )
        )
    if hotspot_id:
        query = query.where(contains(Task.hotspot_id, hotspot_id))
    if period:
        query = query.where(contains(Task.period, period))
    if cursor is not None:
        query = query.where(Task.row_number > cursor)
    rows = list(db.scalars(query).unique())
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].row_number if has_more and rows and sort == "row_number" else None
    pagination = {"next_cursor": next_cursor, "has_more": has_more}
    if sort == "updated_desc":
        pagination["next_page_token"] = updated_token(rows[-1].updated_at, rows[-1].row_number) if has_more and rows else None
    return success(
        [task_view(item).model_dump(mode="json") for item in rows],
        pagination=pagination,
    )


@router.post("/api/v1/tasks/{task_id}/results")
def create_result(
    task_id: str,
    payload: ResultCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    _principal: Principal = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    body = normalized_result_payload(payload)
    request_hash = canonical_json_hash(body)
    task = db.scalar(task_query().where(Task.task_id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "message": "Task not found"})
    if idempotency_key:
        existing = db.scalar(select(TaskResult).where(TaskResult.idempotency_key == idempotency_key))
        if existing:
            existing_matches = existing.request_hash == request_hash or canonical_json_hash(
                stored_result_payload(existing)
            ) == request_hash
            if existing.task_id != task_id or not existing_matches:
                raise HTTPException(
                    status_code=409,
                    detail={"code": "idempotency_conflict", "message": "Idempotency-Key was reused"},
                )
            return success(result_view(existing).model_dump(mode="json"))
    attempt = (db.scalar(select(func.max(TaskResult.attempt)).where(TaskResult.task_id == task_id)) or 0) + 1
    result = TaskResult(
        task_id=task_id,
        attempt=attempt,
        outcome=payload.outcome,
        summary=payload.summary,
        artifact_urls=list(payload.artifact_urls),
        error=payload.error,
        extra_metadata=payload.metadata,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )
    task.status = payload.outcome
    task.updated_at = utc_now()
    db.add(result)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "result_conflict", "message": "Concurrent or duplicate result submission"},
        ) from exc
    db.refresh(result)
    return success(result_view(result).model_dump(mode="json"))
