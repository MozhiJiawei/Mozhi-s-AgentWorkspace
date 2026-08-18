#!/usr/bin/env bash
set -euo pipefail

SOURCE=${1:?usage: update-edge-source.sh <extracted-source-root>}
DEPLOY_PATH=${DEPLOY_PATH:-/opt/mozhi-agent-workspace-services}
COMPOSE="$DEPLOY_PATH/deploy/resource-server/compose.production.yml"
INCOMING="$SOURCE/deploy/resource-server"
TARGET="$DEPLOY_PATH/deploy/resource-server"

[ "$(readlink -m -- "$DEPLOY_PATH")" = "$DEPLOY_PATH" ] || exit 64
case "$DEPLOY_PATH" in /opt/*) ;; *) exit 64 ;; esac
test -f "$COMPOSE"
test -f "$INCOMING/edge/Caddyfile.template"
test -f "$INCOMING/edge/Dockerfile"
test -f "$INCOMING/edge/Dockerfile.source"
test -f "$INCOMING/edge/entrypoint.sh"
test -f "$INCOMING/compose.production.yml"

backup=$(mktemp -d /tmp/mozhi-edge-backup.XXXXXX)
cp -a "$TARGET/edge" "$backup/edge"
cp -a "$COMPOSE" "$backup/compose.production.yml"
if docker image inspect mozhi-agent-service-edge:local >/dev/null 2>&1; then
  docker tag mozhi-agent-service-edge:local mozhi-agent-service-edge:previous
fi

restore() {
  rm -rf "$TARGET/edge"
  cp -a "$backup/edge" "$TARGET/edge"
  cp -a "$backup/compose.production.yml" "$COMPOSE"
  if docker image inspect mozhi-agent-service-edge:previous >/dev/null 2>&1; then
    docker tag mozhi-agent-service-edge:previous mozhi-agent-service-edge:local
    docker compose -f "$COMPOSE" up -d --no-deps --force-recreate edge
  fi
}
finish() {
  rc=$?
  trap - EXIT INT TERM
  if [ "$rc" -ne 0 ]; then
    echo "Edge 发布失败，恢复上一版本。" >&2
    set +e
    restore
    set -e
  fi
  rm -rf "$backup"
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT TERM

rm -rf "$TARGET/edge"
cp -a "$INCOMING/edge" "$TARGET/edge"
cp -a "$INCOMING/compose.production.yml" "$COMPOSE"
cp -a "$INCOMING/scripts/update-edge-source.sh" "$TARGET/scripts/update-edge-source.sh"
docker build \
  --build-arg EDGE_BASE_IMAGE=mozhi-agent-service-edge:previous \
  --file "$TARGET/edge/Dockerfile.source" \
  --tag mozhi-agent-service-edge:local \
  "$DEPLOY_PATH"
docker compose -f "$COMPOSE" up -d --no-deps edge

for attempt in $(seq 1 60); do
  if curl -kfsS https://127.0.0.1/health >/dev/null \
    && curl -fsS --resolve docs.haohaoxiaoyu.top:443:127.0.0.1 https://docs.haohaoxiaoyu.top/healthz >/dev/null \
    && curl -fsS --resolve ccn-api.haohaoxiaoyu.top:443:127.0.0.1 https://ccn-api.haohaoxiaoyu.top/api/v1/health >/dev/null \
    && curl -fsS --resolve inferenceviz.haohaoxiaoyu.top:443:127.0.0.1 https://inferenceviz.haohaoxiaoyu.top/healthz >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    docker logs --tail 120 mozhi-agent-service-edge >&2 || true
    exit 1
  fi
  sleep 2
done
trap - EXIT INT TERM
rm -rf "$backup"
echo "Edge source update succeeded."
