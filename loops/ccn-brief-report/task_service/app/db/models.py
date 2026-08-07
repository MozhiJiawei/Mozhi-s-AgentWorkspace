from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


SQLITE_INTEGER_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class Task(Base):
    __tablename__ = "tasks"

    row_number: Mapped[int] = mapped_column(SQLITE_INTEGER_BIGINT, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    hotspot_id: Mapped[str] = mapped_column(String(128), nullable=False)
    period: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    create_idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    create_request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    results: Mapped[list["TaskResult"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", order_by="TaskResult.attempt"
    )

    __table_args__ = (Index("ix_tasks_status_row_number", "status", "row_number"),)


class TaskResult(Base):
    __tablename__ = "task_results"

    id: Mapped[int] = mapped_column(SQLITE_INTEGER_BIGINT, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    artifact_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text)
    extra_metadata: Mapped[dict[str, object]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    task: Mapped[Task] = relationship(back_populates="results")

    __table_args__ = (Index("uq_task_results_task_attempt", "task_id", "attempt", unique=True),)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(SQLITE_INTEGER_BIGINT, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(256), nullable=False)
    source_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    key_fingerprint: Mapped[str | None] = mapped_column(String(16))
    task_id: Mapped[str | None] = mapped_column(String(128))
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
