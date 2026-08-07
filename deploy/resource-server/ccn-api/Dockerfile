ARG PYTHON_IMAGE=python:3.12-slim-bookworm
FROM ${PYTHON_IMAGE}
ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/ccn-venv/bin:$PATH

RUN python -m venv /opt/ccn-venv \
    && useradd --system --uid 10001 --create-home --home-dir /home/ccn ccn

WORKDIR /app
COPY loops/ccn-brief-report/task_service/pyproject.toml ./
COPY loops/ccn-brief-report/task_service/app ./app
COPY loops/ccn-brief-report/task_service/migrations ./migrations
COPY loops/ccn-brief-report/task_service/alembic.ini ./alembic.ini
RUN pip install --no-cache-dir --index-url "$PIP_INDEX_URL" .

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
