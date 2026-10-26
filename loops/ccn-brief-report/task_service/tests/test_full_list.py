from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.models import Task, TaskResult
from app.domain.schemas import TaskCreate
from app.domain.task_creation import new_task


@pytest.fixture
def mixed_tasks(client, sample_task):
    """Cross both former list limits with all statuses and filterable fields."""
    task_ids = [f"full-list-{index:03}" for index in range(501)]
    with client.db_factory() as db:
        for index, task_id in enumerate(task_ids):
            task = new_task(TaskCreate(**{
                **sample_task,
                "task_id": task_id,
                "hotspot_id": "HS-target" if index % 2 == 0 else "HS-other",
                "period": "2026-W32" if index % 5 == 0 else "2026-W33",
            }))
            task.status = ("pending", "completed", "failed")[index % 3]
            task.updated_at = datetime(
                2026, 9, 2, tzinfo=timezone.utc
            ) if index % 7 == 0 else datetime(2026, 9, 1, 15, 59, tzinfo=timezone.utc)
            db.add(task)
        db.commit()
    return task_ids


def test_one_request_returns_all_mixed_status_tasks(client, api_headers, mixed_tasks):
    response = client.get("/api/v1/tasks", headers=api_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "data"}
    assert body["status"] == "success"
    assert [task["task_id"] for task in body["data"]] == mixed_tasks
    assert [task["row_number"] for task in body["data"]] == list(range(1, 502))
    assert {task["status"] for task in body["data"]} == {"pending", "completed", "failed"}


@pytest.mark.parametrize("sort", ["row_number", "updated_desc"])
def test_obsolete_pagination_parameters_are_ignored(client, api_headers, mixed_tasks, sort):
    expected = client.get("/api/v1/tasks", params={"sort": sort}, headers=api_headers).json()
    for params in (
        {"limit": "1", "cursor": "500", "page_token": "not-a-token"},
        {"limit": "500", "cursor": "999999999999999999999999999", "page_token": ""},
        {"limit": "invalid", "cursor": "-1", "page_token": "x" * 300},
    ):
        response = client.get("/api/v1/tasks", params={"sort": sort, **params}, headers=api_headers)
        assert response.status_code == 200
        assert response.json() == expected
        assert len(response.json()["data"]) == 501


def test_list_openapi_exposes_only_current_filters(client):
    parameters = client.app.openapi()["paths"]["/api/v1/tasks"]["get"]["parameters"]
    query_names = {item["name"] for item in parameters if item["in"] == "query"}
    assert query_names == {"status", "q", "hotspot_id", "period", "sort", "updated_from", "updated_to"}


def test_filters_return_all_matches_and_still_combine(client, api_headers, mixed_tasks):
    for alias, canonical in (("未领取", "pending"), ("已完成", "completed"), ("失败", "failed")):
        response = client.get("/api/v1/tasks", params={"status": alias}, headers=api_headers)
        assert response.status_code == 200
        tasks = response.json()["data"]
        assert len(tasks) == 167
        assert all(task["status"] == canonical for task in tasks)
    for params, count in (({"q": "full-list"}, 501), ({"hotspot_id": "target"}, 251), ({"period": "W32"}, 101)):
        response = client.get("/api/v1/tasks", params=params, headers=api_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == count
    combined = client.get("/api/v1/tasks", params={
        "status": "失败", "q": "full-list", "hotspot_id": "target", "period": "W32",
        "updated_from": "2026-09-02", "updated_to": "2026-09-02", "sort": "updated_desc",
    }, headers=api_headers)
    assert combined.status_code == 200
    assert [task["task_id"] for task in combined.json()["data"]] == ["full-list-350", "full-list-140"]


def test_tasks_beyond_former_limits_support_detail_result_and_delete(client, api_headers, mixed_tasks):
    for task_id in (mixed_tasks[100], mixed_tasks[500]):
        task_url = f"/api/v1/tasks/{task_id}"
        fetched = client.get(task_url, headers=api_headers)
        assert fetched.status_code == 200
        assert fetched.json()["data"]["task_id"] == task_id
        result = client.post(f"{task_url}/results", headers=api_headers, json={
            "outcome": "completed", "artifact_urls": ["https://example.test/report"],
        })
        assert result.status_code == 200
        updated = client.get(task_url, headers=api_headers).json()["data"]
        assert updated["status"] == "completed"
        assert updated["latest_result"]["artifact_urls"] == ["https://example.test/report"]
        listing = client.get("/api/v1/tasks", headers=api_headers).json()["data"]
        assert next(task for task in listing if task["task_id"] == task_id) == updated
        deleted = client.delete(task_url, headers=api_headers)
        assert deleted.status_code == 200
        assert deleted.json()["data"] == {"task_id": task_id, "deleted": True}
        assert client.get(task_url, headers=api_headers).status_code == 404
        with client.db_factory() as db:
            assert db.scalar(select(TaskResult).where(TaskResult.task_id == task_id)) is None
    remaining = client.get("/api/v1/tasks", headers=api_headers).json()["data"]
    assert len(remaining) == 499
    assert {task["task_id"] for task in remaining}.isdisjoint({mixed_tasks[100], mixed_tasks[500]})


def test_empty_list_keeps_success_envelope(client, api_headers):
    for params in ({}, {"q": "missing", "limit": "1", "cursor": "1", "page_token": "old"}):
        response = client.get("/api/v1/tasks", params=params, headers=api_headers)
        assert response.status_code == 200
        assert response.json() == {"status": "success", "data": []}


def test_full_list_preserves_legacy_categories_and_result_urls(client, api_headers, mixed_tasks):
    legacy_task_id = mixed_tasks[500]
    encoded_url = "https://example.test/%E6%8A%A5%E5%91%8A.html"
    with client.db_factory() as db:
        task = db.scalar(select(Task).where(Task.task_id == legacy_task_id))
        task.category = None
        task.status = "completed"
        db.add(TaskResult(
            task_id=legacy_task_id, attempt=1, outcome="completed", artifact_urls=[encoded_url],
            summary=None, error=None, extra_metadata={}, request_hash="legacy-result-hash",
        ))
        db.commit()
    response = client.get("/api/v1/tasks", headers=api_headers)
    assert response.status_code == 200
    tasks = response.json()["data"]
    assert len(tasks) == 501
    assert tasks[0]["category"] is None
    assert tasks[0]["latest_result"] is None
    legacy = tasks[-1]
    assert legacy["task_id"] == legacy_task_id
    assert legacy["category"] is None
    assert legacy["latest_result"]["artifact_urls"] == ["https://example.test/报告.html"]
    assert legacy["latest_result"]["summary"] is None
    with client.db_factory() as db:
        stored = db.scalar(select(TaskResult).where(TaskResult.task_id == legacy_task_id))
        assert stored.artifact_urls == [encoded_url]
