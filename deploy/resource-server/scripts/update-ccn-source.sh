#!/usr/bin/env bash
set -euo pipefail

SOURCE=${1:?usage: update-ccn-source.sh <extracted-source-root>}
DEPLOY_PATH=${DEPLOY_PATH:-/opt/mozhi-agent-workspace-services}
BOOTSTRAP_MOUNT=${BOOTSTRAP_MOUNT:-false}
CONTAINER=ccn-brief-task-api
COMPOSE="$DEPLOY_PATH/deploy/resource-server/compose.production.yml"
TARGET="$DEPLOY_PATH/loops/ccn-brief-report/task_service"
INCOMING="$SOURCE/loops/ccn-brief-report/task_service"

resolved_deploy_path=$(readlink -m -- "$DEPLOY_PATH")
[ "$resolved_deploy_path" = "$DEPLOY_PATH" ] || { echo "DEPLOY_PATH must be normalized: $DEPLOY_PATH" >&2; exit 64; }
case "$DEPLOY_PATH" in /opt/*) ;; *) echo "unsafe DEPLOY_PATH: $DEPLOY_PATH" >&2; exit 64 ;; esac
case "$BOOTSTRAP_MOUNT" in true|false) ;; *) echo "invalid BOOTSTRAP_MOUNT" >&2; exit 64 ;; esac
test -d "$INCOMING/app"
test -f "$INCOMING/pyproject.toml"
test -f "$SOURCE/deploy/resource-server/compose.production.yml"
test -f "$COMPOSE"
docker inspect "$CONTAINER" >/dev/null

test -d "$TARGET/app"
test -d "$TARGET/migrations"
test -d "$INCOMING/migrations"
cmp -s "$INCOMING/pyproject.toml" "$TARGET/pyproject.toml" || {
  echo "pyproject.toml changed; use a full CCN deployment to update dependencies." >&2
  exit 67
}
cmp -s "$INCOMING/alembic.ini" "$TARGET/alembic.ini" || {
  echo "alembic.ini changed; use a full CCN deployment." >&2
  exit 68
}
diff -qr "$INCOMING/migrations" "$TARGET/migrations" >/dev/null || {
  echo "Database migrations changed; use a full CCN deployment." >&2
  exit 69
}

backup=$(mktemp -d /tmp/mozhi-ccn-source-backup.XXXXXX)
mkdir -p "$backup/task_service"
cp -a "$TARGET/." "$backup/task_service/"
cp -a "$COMPOSE" "$backup/compose.production.yml"
update_started=false
compose_changed=false

restore_source() {
  find "$TARGET" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + \
    && cp -a "$backup/task_service/." "$TARGET/" \
    && { [ "$compose_changed" = false ] || cp -a "$backup/compose.production.yml" "$COMPOSE"; } \
    && docker start "$CONTAINER" >/dev/null
}

finish() {
  rc=$?
  trap - EXIT INT TERM
  if [ "$rc" -ne 0 ] && [ "$update_started" = true ]; then
    set +e
    restore_source
    restore_rc=$?
    set -e
    if [ "$restore_rc" -ne 0 ]; then
      echo "Automatic source recovery failed; backup preserved at $backup" >&2
      exit "$rc"
    fi
  fi
  rm -rf "$backup"
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT TERM

mounted_source=$(docker inspect "$CONTAINER" --format '{{range .Mounts}}{{if eq .Destination "/app"}}{{.Source}}{{end}}{{end}}')
if [ -z "$mounted_source" ]; then
  if [ "$BOOTSTRAP_MOUNT" != true ]; then
    echo "CCN source mount is not enabled; rerun once with --bootstrap-mount." >&2
    exit 65
  fi
  cp "$SOURCE/deploy/resource-server/compose.production.yml" "$COMPOSE"
  compose_changed=true
fi

update_started=true
docker stop "$CONTAINER" >/dev/null
find "$TARGET" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
cp -a "$INCOMING/." "$TARGET/"

if [ -z "$mounted_source" ]; then
  docker compose -f "$COMPOSE" up -d --no-deps --no-build --force-recreate ccn-api
else
  expected=$(readlink -f "$TARGET")
  actual=$(readlink -f "$mounted_source")
  [ "$actual" = "$expected" ] || { echo "unexpected /app mount: $actual" >&2; exit 66; }
  docker start "$CONTAINER" >/dev/null
fi

for attempt in $(seq 1 60); do
  status=$(docker inspect "$CONTAINER" --format '{{.State.Health.Status}}' 2>/dev/null || true)
  [ "$status" = healthy ] && break
  if [ "$attempt" -eq 60 ]; then
    docker logs --tail 120 "$CONTAINER" >&2 || true
    echo "CCN API did not become healthy after source update." >&2
    exit 1
  fi
  sleep 2
done

python3 "$DEPLOY_PATH/deploy/resource-server/scripts/smoke-test.py" --internal --skip-write
echo "CCN source update succeeded; image was not built."
