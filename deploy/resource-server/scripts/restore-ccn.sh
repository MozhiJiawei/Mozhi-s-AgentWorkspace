#!/usr/bin/env bash
set -euo pipefail

BACKUP=${1:?usage: CONFIRM_RESTORE=restore restore-ccn.sh <backup.dump>}
[ "${CONFIRM_RESTORE:-}" = restore ] || { echo "Set CONFIRM_RESTORE=restore" >&2; exit 64; }
[ -f "$BACKUP" ] || { echo "Backup not found: $BACKUP" >&2; exit 66; }
DEPLOY_PATH=${DEPLOY_PATH:-/opt/mozhi-agent-workspace-services}
COMPOSE=${COMPOSE_FILE:-$DEPLOY_PATH/deploy/resource-server/compose.production.yml}
BACKUP_SCRIPT=${BACKUP_SCRIPT:-$DEPLOY_PATH/deploy/resource-server/scripts/backup-ccn.sh}
CONTAINER=${CCN_POSTGRES_CONTAINER:-ccn-brief-postgres}
docker exec -i "$CONTAINER" pg_restore --list < "$BACKUP" >/dev/null
bash "$BACKUP_SCRIPT" >/dev/null
docker compose -f "$COMPOSE" stop ccn-api
docker exec "$CONTAINER" sh -c 'dropdb --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
docker exec -i "$CONTAINER" sh -c 'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < "$BACKUP"
docker compose -f "$COMPOSE" up -d --no-deps ccn-api
