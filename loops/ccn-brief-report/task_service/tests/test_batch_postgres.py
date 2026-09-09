"""Opt-in real PostgreSQL tests; each run owns an isolated schema."""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.api.batch import create_tasks
from app.db.models import Task
from app.domain.schemas import TaskBatchCreate


@pytest.fixture
def postgres():
    url = os.environ.get("CCN_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set CCN_TEST_POSTGRES_URL to run real transaction tests")
    schema = "batch_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as db:
        db.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped_url = make_url(url).update_query_dict({"options": f"-csearch_path={schema}"})
    engine = create_engine(scoped_url)
    try:
        result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                       cwd=Path(__file__).resolve().parents[1], check=False, capture_output=True,
                       env={**os.environ, "DATABASE_URL": scoped_url.render_as_string(hide_password=False)})
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as db:
            db.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def submit(engine, tasks, key=None, barrier=None):
    with Session(engine, expire_on_commit=False) as db:
        if barrier:
            def rendezvous(*_):
                barrier.wait(timeout=10)
            event.listen(db, "before_flush", rendezvous, once=True)
        return create_tasks(TaskBatchCreate(tasks=tasks), Request({"type": "http"}), key, None, db)


@pytest.mark.parametrize("key", [None, "concurrent-key"])
def test_concurrent_identical_batches(postgres, sample_task, key):
    tasks = [sample_task, {**sample_task, "task_id": "second"}]
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, postgres, tasks, key, barrier) for _ in range(2)]
        responses = [f.result(timeout=20) for f in futures]
    assert sorted(r.status_code for r in responses) == ([201, 201] if key else [200, 201])
    if key:
        assert responses[0].body == responses[1].body
    with Session(postgres) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 2


def test_conflicting_race_is_atomic(postgres, sample_task):
    barrier = Barrier(2)
    def run(label):
        tasks = [{**sample_task, "content": label}, {**sample_task, "task_id": label}]
        try:
            return submit(postgres, tasks, barrier=barrier).status_code
        except HTTPException as error:
            return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, ["one", "two"])) == [201, 409]
    with Session(postgres) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 2


def test_failure_after_flush_rolls_back(postgres, sample_task):
    with pytest.raises(RuntimeError), Session(postgres) as db:
        def fail(*_):
            raise RuntimeError("Injected failure after INSERTs")
        event.listen(db, "after_flush_postexec", fail, once=True)
        create_tasks(TaskBatchCreate(tasks=[sample_task, {**sample_task, "task_id": "second"}]),
                     Request({"type": "http"}), "rollback", None, db)
    with Session(postgres) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
    assert submit(postgres, [sample_task], "rollback").status_code == 201


def test_concurrent_same_key_different_payload(postgres, sample_task):
    barrier = Barrier(2)
    def run(task_id):
        try:
            return submit(postgres, [{**sample_task, "task_id": task_id}], "shared", barrier).status_code
        except HTTPException as error:
            return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, ["one", "two"])) == [201, 409]
    with Session(postgres) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 1
