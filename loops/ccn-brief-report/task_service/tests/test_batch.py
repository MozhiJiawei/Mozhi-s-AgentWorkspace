import json

import pytest
from sqlalchemy import func, select

from app.db.models import BatchCreation, Task


def batch(client, headers, tasks, key=None):
    return client.post("/api/v1/tasks/batch", headers={**headers, **({"Idempotency-Key": key} if key else {})}, json={"tasks": tasks})


@pytest.mark.parametrize("count,code", [(0, 422), (1, 201), (200, 201), (201, 422)])
def test_size(client, api_headers, sample_task, count, code):
    response = batch(client, api_headers, [{**sample_task, "task_id": f"t-{i}"} for i in range(count)])
    assert response.status_code == code
    with client.db_factory() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == (count if code == 201 else 0)


def test_atomic_conflict_and_order(client, api_headers, sample_task):
    assert batch(client, api_headers, [sample_task]).status_code == 201
    new = {**sample_task, "task_id": "new"}
    response = batch(client, api_headers, [new, {**sample_task, "content": "different"}])
    assert response.status_code == 409
    assert response.json()["error"]["details"] == [{"index": 1, "task_id": sample_task["task_id"]}]
    assert client.get("/api/v1/tasks/new", headers=api_headers).status_code == 404
    response = batch(client, api_headers, [new, sample_task])
    assert response.status_code == 201
    assert [i["disposition"] for i in response.json()["data"]["items"]] == ["created", "existing"]
    assert batch(client, api_headers, [new, sample_task]).status_code == 200


@pytest.mark.parametrize("change", [{"url": "http://example.com"}, {"category": "invalid"}, {"content": "x" * 100001}])
def test_validation_is_located_and_atomic(client, api_headers, sample_task, change):
    response = batch(client, api_headers, [sample_task, {**sample_task, "task_id": "invalid", **change}])
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["location"][:3] == ["body", "tasks", 1]
    with client.db_factory() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


def test_duplicate_located(client, api_headers, sample_task):
    response = batch(client, api_headers, [sample_task, sample_task])
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["location"] == ["body", "tasks", 1, "task_id"]


def test_key_retained_after_delete_and_order_matters(client, api_headers, sample_task):
    tasks = [sample_task, {**sample_task, "task_id": "other"}]
    first = batch(client, api_headers, tasks, "key")
    assert first.status_code == 201
    assert batch(client, api_headers, tasks, "key").json() == first.json()
    assert batch(client, api_headers, tasks[::-1], "key").status_code == 409
    client.delete("/api/v1/tasks/other", headers=api_headers)
    assert batch(client, api_headers, tasks, "key").json() == first.json()
    assert client.get("/api/v1/tasks/other", headers=api_headers).status_code == 404
    with client.db_factory() as db:
        assert db.get(BatchCreation, "key") is not None


def test_legacy_identity_and_status(client, api_headers, sample_task):
    client.post("/api/v1/tasks", headers={**api_headers, "Idempotency-Key": "shared"}, json=sample_task)
    client.post(f'/api/v1/tasks/{sample_task["task_id"]}/results', headers=api_headers,
                json={"outcome": "completed", "summary": "done"})
    response = batch(client, api_headers, [{**sample_task, "category": None}], "shared")
    assert response.status_code == 200
    with client.db_factory() as db:
        task = db.scalar(select(Task))
        task.content = "later edited content"
        db.commit()
    assert batch(client, api_headers, [sample_task]).status_code == 200
    assert client.get(f'/api/v1/tasks/{sample_task["task_id"]}', headers=api_headers).json()["data"]["status"] == "completed"


def test_byte_limit_chunked_and_utf8(client, api_headers, sample_task):
    payload = json.dumps({"tasks": [{**sample_task, "task_id": f"t-{i}", "content": "中" * 100000} for i in range(40)]}, ensure_ascii=False).encode()
    response = client.post("/api/v1/tasks/batch", headers={**api_headers, "Content-Type": "application/json"}, content=iter([payload[:1000], payload[1000:]]))
    assert response.status_code == 413
    with client.db_factory() as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


def test_one_write_limit_and_auth(client, api_headers, sample_task):
    assert batch(client, {}, [sample_task]).status_code == 401
    client.fake_limiter.calls.clear()
    assert batch(client, api_headers, [sample_task]).status_code == 201
    assert len(client.fake_limiter.calls) == 1
    assert client.fake_limiter.calls[0][0] == "write"


def test_exact_body_limit_and_openapi(client, api_headers, sample_task):
    raw = json.dumps({"tasks": [sample_task]}).encode()
    headers = {**api_headers, "Content-Type": "application/json"}
    padded = raw + b" " * (10 * 1024 * 1024 - len(raw))
    assert client.post("/api/v1/tasks/batch", headers=headers, content=padded).status_code == 201
    assert client.post("/api/v1/tasks/batch", headers=headers, content=padded + b" ").status_code == 413
    from app.main import app
    operation = app.openapi()["paths"]["/api/v1/tasks/batch"]["post"]
    assert {"200", "201", "413", "422"} <= operation["responses"].keys()


def test_download_assets_are_local_and_bounded(client):
    page = client.get("/dashboard").text
    for asset in ("downloads.js", "fflate-0.8.2.js"):
        assert f"/dashboard-assets/{asset}" in page
        assert client.get(f"/dashboard-assets/{asset}").status_code == 200
    assert client.get("/dashboard-assets/not-allowed.js").status_code == 404
    assert "code-batch-create" in page
    assert "全选当前页" in page


def test_batch_audit_counts_and_literal_task_id(client, api_headers, sample_task, monkeypatch):
    from app.db.models import AuditEvent
    import app.main
    monkeypatch.setattr(app.main, "SessionLocal", client.db_factory)
    assert batch(client, api_headers, [{**sample_task, "task_id": "batch"}]).status_code == 201
    assert client.get("/api/v1/tasks/batch", headers=api_headers).status_code == 200
    with client.db_factory() as db:
        events = list(db.scalars(select(AuditEvent).order_by(AuditEvent.id)))
        assert events[0].task_id is None
        assert events[0].batch_counts == {"requested": 1, "created": 1, "existing": 0}
        assert events[1].task_id == "batch"
