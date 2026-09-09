import base64
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.models import Task


def seed(client, headers, sample, stamps):
    for index, stamp in enumerate(stamps):
        payload = {**sample, "task_id": f"date-{index}"}
        assert client.post("/api/v1/tasks", headers=headers, json=payload).status_code == 201
        with client.db_factory() as db:
            task = db.scalar(select(Task).where(Task.task_id == payload["task_id"]))
            task.updated_at = datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)
            db.commit()


def test_updated_order_with_ties_and_legacy_paging(client, api_headers, sample_task):
    seed(client, api_headers, sample_task, ["2026-09-01T12:00:00", "2026-09-09T12:00:00", "2026-09-05T12:00:00", "2026-09-09T12:00:00"])
    first = client.get("/api/v1/tasks?sort=updated_desc&limit=2", headers=api_headers).json()
    assert [t["task_id"] for t in first["data"]] == ["date-3", "date-1"]
    token = first["pagination"]["next_page_token"]
    second = client.get("/api/v1/tasks", params={"sort": "updated_desc", "limit": 2, "page_token": token}, headers=api_headers).json()
    assert [t["task_id"] for t in second["data"]] == ["date-2", "date-0"]
    assert not second["pagination"]["has_more"]
    legacy = client.get("/api/v1/tasks?limit=2", headers=api_headers).json()
    assert [t["task_id"] for t in legacy["data"]] == ["date-0", "date-1"]
    assert legacy["pagination"]["next_cursor"] == 2


def test_beijing_inclusive_day_boundaries(client, api_headers, sample_task):
    seed(client, api_headers, sample_task, ["2026-09-01T15:59:59.999999", "2026-09-01T16:00:00", "2026-09-03T15:59:59.999999", "2026-09-03T16:00:00"])
    params = {"sort": "updated_desc", "updated_from": "2026-09-02", "updated_to": "2026-09-03"}
    data = client.get("/api/v1/tasks", params=params, headers=api_headers).json()["data"]
    assert [t["task_id"] for t in data] == ["date-2", "date-1"]
    params["q"] = "date-1"
    assert len(client.get("/api/v1/tasks", params=params, headers=api_headers).json()["data"]) == 1
    params.update(updated_from="2026-10-01", updated_to="2026-10-02")
    assert client.get("/api/v1/tasks", params=params, headers=api_headers).json()["data"] == []


@pytest.mark.parametrize("query", [
    "updated_from=2026-09-10&updated_to=2026-09-01", "updated_from=bad", "updated_to=9999-12-31",
    "sort=unknown", "sort=updated_desc&cursor=2", "page_token=abc", "sort=updated_desc&page_token=not-a-token",
])
def test_invalid_filters(client, api_headers, query):
    assert client.get("/api/v1/tasks?" + query, headers=api_headers).status_code == 422


def test_cursor_survives_anchor_deletion(client, api_headers, sample_task):
    seed(client, api_headers, sample_task, ["2026-09-01T12:00:00", "2026-09-09T12:00:00"])
    page = client.get("/api/v1/tasks?sort=updated_desc&limit=1", headers=api_headers).json()
    client.delete("/api/v1/tasks/date-1", headers=api_headers)
    next_page = client.get("/api/v1/tasks", params={"sort": "updated_desc", "page_token": page["pagination"]["next_page_token"]}, headers=api_headers).json()
    assert [t["task_id"] for t in next_page["data"]] == ["date-0"]


@pytest.mark.parametrize("outcome", ["completed", "failed"])
def test_same_status_result_updates_date_but_replay_does_not(client, api_headers, sample_task, monkeypatch, outcome):
    seed(client, api_headers, sample_task, ["2026-09-01T12:00:00", "2026-09-08T12:00:00"])
    result_url = "/api/v1/tasks/date-0/results"
    monkeypatch.setattr("app.api.routes.utc_now", lambda: datetime(2026, 9, 1, 12, tzinfo=timezone.utc))
    initial = {"outcome": outcome, "summary": "first", "error": "test failure" if outcome == "failed" else None}
    assert client.post(result_url, headers=api_headers, json=initial).status_code == 200
    monkeypatch.setattr("app.api.routes.utc_now", lambda: datetime(2026, 9, 9, 12, tzinfo=timezone.utc))
    headers = {**api_headers, "Idempotency-Key": "revised-result"}
    result = {**initial, "summary": "revised"}
    assert client.post(result_url, headers=headers, json=result).status_code == 200
    listing = client.get("/api/v1/tasks?sort=updated_desc", headers=api_headers).json()["data"]
    assert [task["task_id"] for task in listing] == ["date-0", "date-1"]
    filtered = client.get("/api/v1/tasks?updated_from=2026-09-09&updated_to=2026-09-09", headers=api_headers).json()["data"]
    assert [task["task_id"] for task in filtered] == ["date-0"]
    before = client.get("/api/v1/tasks/date-0", headers=api_headers).json()["data"]
    monkeypatch.setattr("app.api.routes.utc_now", lambda: datetime(2026, 9, 10, 12, tzinfo=timezone.utc))
    assert client.post(result_url, headers=headers, json=result).status_code == 200
    after = client.get("/api/v1/tasks/date-0", headers=api_headers).json()["data"]
    assert after["updated_at"] == before["updated_at"]
    assert after["latest_result"] == before["latest_result"]


@pytest.mark.parametrize("cursor", [
    ["0001-01-01T00:00:00+08:00", 1],
    ["9999-12-31T23:00:00-08:00", 1],
    ["2026-09-09T00:00:00+00:00", 2**63],
    ["2026-09-09T00:00:00+00:00", 10**50],
])
def test_cursor_outside_storage_range_returns_422(client, api_headers, cursor):
    token = base64.urlsafe_b64encode(json.dumps(cursor).encode()).decode().rstrip("=")
    response = client.get("/api/v1/tasks", params={"sort": "updated_desc", "page_token": token}, headers=api_headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_page_token"
