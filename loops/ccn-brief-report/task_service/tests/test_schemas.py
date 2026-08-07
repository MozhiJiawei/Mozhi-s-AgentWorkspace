from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.schemas import ResultCreate, TaskCreate


@pytest.mark.parametrize("task_id", ["../../unsafe", ".hidden", "-task"])
def test_task_id_matches_loop_client_contract(task_id):
    with pytest.raises(ValidationError):
        TaskCreate(
            task_id=task_id,
            content="x",
            url="https://example.test",
            hotspot_id="HS",
            period="2026-W32",
        )


def test_task_source_requires_https():
    with pytest.raises(ValidationError):
        TaskCreate(
            task_id="TASK-1",
            content="x",
            url="http://example.test/source",
            hotspot_id="HS",
            period="2026-W32",
        )


def test_failed_result_requires_error():
    with pytest.raises(ValidationError):
        ResultCreate(outcome="failed")
