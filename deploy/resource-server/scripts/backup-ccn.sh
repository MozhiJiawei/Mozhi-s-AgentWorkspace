#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT=${BACKUP_ROOT:-/var/backups/mozhi-agent-workspace/ccn-brief-report}
CONTAINER=${CCN_POSTGRES_CONTAINER:-ccn-brief-postgres}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUTPUT="$BACKUP_ROOT/ccn-$STAMP.dump"
mkdir -p "$BACKUP_ROOT"
chmod 700 "$BACKUP_ROOT"
docker exec "$CONTAINER" sh -c 'exec pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$OUTPUT"
test -s "$OUTPUT"
docker exec -i "$CONTAINER" pg_restore --list < "$OUTPUT" >/dev/null
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
echo "$OUTPUT"
