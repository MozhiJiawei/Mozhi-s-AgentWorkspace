import importlib.util
import json
import re
from html import unescape
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.api.routes import canonical_json_hash
from app.domain.categories import CATEGORY_VALUES
from app.main import app


@pytest.mark.parametrize('category', sorted(CATEGORY_VALUES))
def test_all_categories_roundtrip(client, api_headers, sample_task, category):
    payload = {**sample_task, 'category': category}
    result = client.post('/api/v1/tasks', headers=api_headers, json=payload)
    assert result.status_code == 201
    assert result.json()['data']['category'] == category
    assert client.get('/api/v1/tasks', headers=api_headers).json()['data'][0]['category'] == category
    assert client.get('/api/v1/tasks/'+sample_task['task_id'], headers=api_headers).json()['data']['category'] == category


@pytest.mark.parametrize('category', ['', 'AI模型', '04-AI模型/其他', '04-AI模型/Agent架构与编排', 4, []])
def test_invalid_category_rejected(client, api_headers, sample_task, category):
    assert client.post('/api/v1/tasks', headers=api_headers, json={**sample_task,'category':category}).status_code == 422


def test_null_legacy_idempotency_and_conflict(client, api_headers, sample_task):
    from app.db.models import Task
    headers = {**api_headers, 'Idempotency-Key':'legacy-create'}
    assert client.post('/api/v1/tasks', headers=headers, json=sample_task).status_code == 201
    with client.db_factory() as db:
        stored = db.scalar(sa.select(Task))
        assert stored.create_request_hash == canonical_json_hash(sample_task)
        assert stored.category is None
    again = client.post('/api/v1/tasks', headers=headers, json={**sample_task,'category':None})
    assert again.status_code == 201 and again.json()['data']['category'] is None
    assert client.post('/api/v1/tasks', headers=headers, json={**sample_task,'category':'04-AI模型'}).status_code == 409


def test_docs_and_openapi_share_all_values(client):
    import html
    page = client.get('/dashboard').text
    assert len(CATEGORY_VALUES) == 63
    for value in CATEGORY_VALUES:
        assert 'value="'+html.escape(value, quote=True)+'"' in page
    assert 'id="category-enum-table"' not in page
    assert page.count('data-copy-target="code-create"') == 1
    assert '422' in page and '填写规则' in page
    assert set(app.openapi()['components']['schemas']['Category']['enum']) == CATEGORY_VALUES


def test_migration_preserves_historical_row():
    path = Path(__file__).resolve().parents[1]/'migrations/versions/0002_task_category.py'
    spec = importlib.util.spec_from_file_location('migration_category', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(sa.text('CREATE TABLE tasks (task_id TEXT PRIMARY KEY)'))
        connection.execute(sa.text("INSERT INTO tasks VALUES ('old')"))
        module.op = Operations(MigrationContext.configure(connection))
        module.upgrade()
        assert connection.execute(sa.text('SELECT task_id, category FROM tasks')).one() == ('old',None)
    engine.dispose()


def test_creation_command_is_self_contained(client):
    page = client.get('/dashboard').text
    command = unescape(re.search(r'<code id="code-create">(.*?)</code>', page, re.S).group(1))
    assert '$ApiBase = "https://ccn-api.haohaoxiaoyu.top"' in command
    assert '$ApiKey = "<API_KEY>"' in command
    assert 'category   = $null' in command
    assert 'Invoke-RestMethod' in command
    assert 'category-example-' not in page


def test_category_download_is_public_utf8_and_matches_registry(client):
    from app.domain.category_data import CATEGORY_DETAILS

    response = client.get('/dashboard/categories.txt')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/plain; charset=utf-8'
    assert response.headers['content-disposition'] == 'attachment; filename="ccn-category-labels.txt"'
    labels = response.content.decode('utf-8').splitlines()
    assert labels == [item['value'] for item in CATEGORY_DETAILS]
    assert len(labels) == len(set(labels)) == 63
    page = client.get('/dashboard').text
    assert 'href="/dashboard/categories.txt"' in page
    assert '下载分类标签' in page
