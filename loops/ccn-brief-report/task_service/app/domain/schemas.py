from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from app.domain.task_contract import TASK_ID_PATTERN, is_valid_https_url
from app.domain.urls import normalize_http_iri


class TaskCreate(BaseModel):
    task_id: str = Field(min_length=1, max_length=128, pattern=TASK_ID_PATTERN.pattern)
    content: str = Field(min_length=1, max_length=100_000)
    url: HttpUrl
    hotspot_id: str = Field(min_length=1, max_length=128)
    period: str = Field(min_length=1, max_length=64)

    @field_validator("url")
    @classmethod
    def validate_source_url(cls, value: HttpUrl) -> HttpUrl:
        if not is_valid_https_url(str(value)):
            raise ValueError("url must use HTTPS")
        return value


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
