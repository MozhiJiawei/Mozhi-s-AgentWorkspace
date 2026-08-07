from __future__ import annotations

from app.api.routes import canonical_json_hash
from app.db.models import TaskResult


def create_task(client, headers, payload, key="create-1"):
    return client.post(
        "/api/v1/tasks",
        headers={**headers, "Idempotency-Key": key},
        json=payload,
    )


def test_authentication_requires_the_single_key(client, sample_task, api_headers):
    assert client.get("/api/v1/tasks").status_code == 401
    assert client.delete(f"/api/v1/tasks/{sample_task['task_id']}").status_code == 401
    assert client.get("/api/v1/tasks", headers={"Authorization": "Bearer wrong-key"}).status_code == 401
    assert create_task(client, api_headers, sample_task).status_code == 201
    assert client.get("/api/v1/tasks", headers=api_headers).status_code == 200


def test_create_fetch_and_list_contract(client, sample_task, api_headers):
    created = create_task(client, api_headers, sample_task)
    assert created.status_code == 201
    task = created.json()["data"]
    assert task["row_number"] == 1
    assert task["status"] == "pending"

    fetched = client.get(f"/api/v1/tasks/{sample_task['task_id']}", headers=api_headers)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["task_id"] == sample_task["task_id"]

    listed = client.get("/api/v1/tasks?status=未领取", headers=api_headers).json()
    assert [item["task_id"] for item in listed["data"]] == [sample_task["task_id"]]

    for query in ("q=20260804", "q=HS-1", "hotspot_id=HS", "period=W32"):
        filtered = client.get(f"/api/v1/tasks?{query}", headers=api_headers).json()
        assert [item["task_id"] for item in filtered["data"]] == [sample_task["task_id"]]
    empty = client.get("/api/v1/tasks?q=not-present", headers=api_headers).json()
    assert empty["data"] == []

def test_create_is_idempotent_and_rejects_conflicting_data(client, sample_task, api_headers):
    first = create_task(client, api_headers, sample_task)
    second = create_task(client, api_headers, sample_task)
    assert first.status_code == second.status_code == 201
    assert first.json()["data"]["row_number"] == second.json()["data"]["row_number"]

    changed = {**sample_task, "content": "different"}
    conflict = create_task(client, api_headers, changed)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "task_conflict"


def test_results_are_append_only_and_update_task_status(client, sample_task, api_headers):
    create_task(client, api_headers, sample_task)
    failed = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers={**api_headers, "Idempotency-Key": "result-1"},
        json={"outcome": "failed", "error": "source unavailable", "metadata": {"retry": True}},
    )
    assert failed.status_code == 200
    assert failed.json()["data"]["attempt"] == 1

    completed_payload = {
        "outcome": "completed",
        "artifact_urls": ["https://example.test/report/tree/main/report-directory"],
    }
    completed = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers={**api_headers, "Idempotency-Key": "result-2"},
        json=completed_payload,
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["attempt"] == 2

    repeated = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers={**api_headers, "Idempotency-Key": "result-2"},
        json=completed_payload,
    )
    assert repeated.status_code == 200
    assert repeated.json()["data"]["attempt"] == 2

    task = client.get(f"/api/v1/tasks/{sample_task['task_id']}", headers=api_headers).json()["data"]
    assert task["status"] == "completed"
    assert task["latest_result"]["attempt"] == 2


def test_artifact_urls_are_normalized_to_unicode_before_idempotency(client, sample_task, api_headers):
    create_task(client, api_headers, sample_task)
    encoded_url = (
        "https://github.com/MozhiJiawei/ccn-report/tree/main/"
        "%E5%AD%A6%E6%9C%AF%E8%AE%BA%E6%96%87%E5%88%86%E6%9E%90/Agent/report"
    )
    unicode_url = "https://github.com/MozhiJiawei/ccn-report/tree/main/学术论文分析/Agent/report"

    first = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers={**api_headers, "Idempotency-Key": "unicode-result"},
        json={"outcome": "completed", "artifact_urls": [encoded_url]},
    )
    repeated = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers={**api_headers, "Idempotency-Key": "unicode-result"},
        json={"outcome": "completed", "artifact_urls": [unicode_url]},
    )

    assert first.status_code == repeated.status_code == 200
    assert first.json()["data"]["artifact_urls"] == [unicode_url]
    assert repeated.json()["data"]["artifact_urls"] == [unicode_url]
    assert repeated.json()["data"]["attempt"] == 1
    fetched = client.get(f"/api/v1/tasks/{sample_task['task_id']}", headers=api_headers)
    assert fetched.json()["data"]["latest_result"]["artifact_urls"] == [unicode_url]


def test_legacy_encoded_request_hash_remains_idempotent_without_rewriting_database(
    client, sample_task, api_headers
):
    create_task(client, api_headers, sample_task)
    encoded_url = (
        "https://github.com/MozhiJiawei/ccn-report/tree/main/"
        "%E5%AD%A6%E6%9C%AF%E8%AE%BA%E6%96%87%E5%88%86%E6%9E%90/Agent/report"
    )
    unicode_url = "https://github.com/MozhiJiawei/ccn-report/tree/main/学术论文分析/Agent/report"
    legacy_payload = {
        "outcome": "completed",
        "summary": None,
        "artifact_urls": [encoded_url],
        "error": None,
        "metadata": {},
    }
    with client.db_factory() as session:
        session.add(
            TaskResult(
                task_id=sample_task["task_id"],
                attempt=1,
                outcome="completed",
                summary=None,
                artifact_urls=[encoded_url],
                error=None,
                extra_metadata={},
                idempotency_key="legacy-result",
                request_hash=canonical_json_hash(legacy_payload),
            )
        )
        session.commit()

    repeated = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers={**api_headers, "Idempotency-Key": "legacy-result"},
        json={"outcome": "completed", "artifact_urls": [unicode_url]},
    )

    assert repeated.status_code == 200
    assert repeated.json()["data"]["attempt"] == 1
    assert repeated.json()["data"]["artifact_urls"] == [unicode_url]
    with client.db_factory() as session:
        stored = session.query(TaskResult).filter_by(idempotency_key="legacy-result").one()
        assert stored.artifact_urls == [encoded_url]


def test_delete_task_is_cascading_and_idempotent(client, sample_task, api_headers):
    create_task(client, api_headers, sample_task)
    result = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers={**api_headers, "Idempotency-Key": "delete-result-1"},
        json={"outcome": "completed", "summary": "ready to delete"},
    )
    assert result.status_code == 200

    deleted = client.delete(f"/api/v1/tasks/{sample_task['task_id']}", headers=api_headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"] == {"task_id": sample_task["task_id"], "deleted": True}
    assert client.get(f"/api/v1/tasks/{sample_task['task_id']}", headers=api_headers).status_code == 404

    repeated = client.delete(f"/api/v1/tasks/{sample_task['task_id']}", headers=api_headers)
    assert repeated.status_code == 200
    assert repeated.json()["data"] == {"task_id": sample_task["task_id"], "deleted": False}


def test_batch_delete_removes_selected_tasks_in_one_request(client, sample_task, api_headers):
    task_ids = []
    for index in range(3):
        payload = {**sample_task, "task_id": f"BATCH-{index}"}
        response = create_task(client, api_headers, payload, key=f"batch-create-{index}")
        assert response.status_code == 201
        task_ids.append(payload["task_id"])

    response = client.request(
        "DELETE",
        "/api/v1/tasks",
        headers=api_headers,
        json={"task_ids": [task_ids[0], task_ids[2], "BATCH-MISSING", task_ids[0]]},
    )
    assert response.status_code == 200
    assert response.json()["data"] == {
        "requested": 3,
        "deleted": 2,
        "missing": ["BATCH-MISSING"],
    }
    assert client.get(f"/api/v1/tasks/{task_ids[0]}", headers=api_headers).status_code == 404
    assert client.get(f"/api/v1/tasks/{task_ids[1]}", headers=api_headers).status_code == 200
    assert client.get(f"/api/v1/tasks/{task_ids[2]}", headers=api_headers).status_code == 404


def test_result_validation_and_error_envelope(client, sample_task, api_headers):
    create_task(client, api_headers, sample_task)
    response = client.post(
        f"/api/v1/tasks/{sample_task['task_id']}/results",
        headers=api_headers,
        json={"outcome": "completed"},
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_status_is_rejected(client, api_headers):
    response = client.get("/api/v1/tasks?status=unknown", headers=api_headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_status"


def test_dashboard_is_public_shell_but_data_remains_protected(client):
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "CCN 任务状态台" in dashboard.text
    assert "API 接口文档" in dashboard.text
    assert "Invoke-RestMethod" in dashboard.text
    assert "-Method Delete" in dashboard.text
    assert "删除选中" in dashboard.text
    assert "确认删除任务" in dashboard.text
    assert "&lt;API_KEY&gt;" in dashboard.text
    assert "PRODUCER_API_KEY" not in dashboard.text
    assert "WORKER_API_KEY" not in dashboard.text
    assert "default-src 'self'" in dashboard.headers["content-security-policy"]
    assert "single-test-key" not in dashboard.text
    dashboard_js = client.get("/dashboard-assets/dashboard.js")
    assert dashboard_js.status_code == 200
    assert dashboard_js.headers["cache-control"] == "no-store"
    assert "navigator.clipboard.writeText" in dashboard_js.text
    assert "task.latest_result?.artifact_urls?.[0]" in dashboard_js.text
    assert "JSON.stringify(task.latest_result" not in dashboard_js.text
    assert "task.latest_result?.summary" not in dashboard_js.text
    assert "task.latest_result?.error" not in dashboard_js.text
    assert 'dashboard.js?v=3' in dashboard.text
    assert client.get("/api/v1/tasks").status_code == 401
    assert client.get("/exec", headers={"Authorization": "Bearer single-test-key"}).status_code == 404
