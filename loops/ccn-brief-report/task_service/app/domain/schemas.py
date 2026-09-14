from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from app.domain.task_contract import TASK_ID_PATTERN
from app.domain.urls import normalize_http_iri
from app.domain.categories import Category


class TaskCreate(BaseModel):
    category: Category | None = Field(default=None, description="可选归档约束：完整一级或二级分类路径；省略或null表示AI自动分类")
    task_id: str = Field(min_length=1, max_length=128, pattern=TASK_ID_PATTERN.pattern)
    content: str = Field(min_length=1, max_length=100_000)
    url: HttpUrl
    hotspot_id: str = Field(min_length=1, max_length=128)
    period: str = Field(min_length=1, max_length=64)

class TaskBatchCreate(BaseModel):
    tasks: list[TaskCreate] = Field(min_length=1, max_length=200)

    @field_validator("tasks")
    @classmethod
    def unique_ids(cls, values):
        from pydantic import ValidationError
        seen = set()
        errors = []
        for index, item in enumerate(values):
            if item.task_id in seen:
                errors.append({"type": "value_error", "loc": (index, "task_id"),
                               "input": item.task_id, "ctx": {"error": ValueError("Duplicate task_id")}})
            seen.add(item.task_id)
        if errors:
            raise ValidationError.from_exception_data(cls.__name__, errors)
        return values


class TaskBatchItem(BaseModel):
    index: int
    task_id: str
    disposition: Literal["created", "existing"]


class TaskBatchData(BaseModel):
    requested: int
    created: int
    existing: int
    items: list[TaskBatchItem]


class TaskBatchResponse(BaseModel):
    status: Literal["success"]
    data: TaskBatchData


class TaskBatchDelete(BaseModel):
    task_ids: list[str] = Field(min_length=1, max_length=200)

    @field_validator("task_ids")
    @classmethod
    def validate_task_ids(cls, values: list[str]) -> list[str]:
        if any(not TASK_ID_PATTERN.fullmatch(value) for value in values):
            raise ValueError("task_ids contains an invalid task ID")
        return list(dict.fromkeys(values))


class ResultCreate(BaseModel):
    outcome: Literal["completed", "failed"]
    summary: str | None = Field(default=None, max_length=100_000)
    artifact_urls: list[str] = Field(default_factory=list, max_length=100)
    error: str | None = Field(default=None, max_length=20_000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("artifact_urls")
    @classmethod
    def validate_artifact_urls(cls, values: list[str]) -> list[str]:
        for value in values:
            normalize_http_iri(value)
        return values

    @model_validator(mode="after")
    def validate_outcome_fields(self) -> "ResultCreate":
        if self.outcome == "completed" and not (self.summary or self.artifact_urls):
            raise ValueError("completed result requires summary or artifact_urls")
        if self.outcome == "failed" and not self.error:
            raise ValueError("failed result requires error")
        return self


class ResultView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt: int
    outcome: str
    summary: str | None
    artifact_urls: list[str]
    error: str | None
    metadata: dict[str, Any]
    created_at: datetime


class TaskView(BaseModel):
    category: Category | None = None
    row_number: int
    task_id: str
    content: str
    url: str
    hotspot_id: str
    period: str
    status: str
    created_at: datetime
    updated_at: datetime
    latest_result: ResultView | None = None
