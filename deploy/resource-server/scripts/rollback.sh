#!/usr/bin/env bash
set -euo pipefail

COMPONENT=${COMPONENT:-all}
DEPLOY_PATH=${DEPLOY_PATH:-/opt/mozhi-agent-workspace-services}
COMPOSE="$DEPLOY_PATH/deploy/resource-server/compose.production.yml"
PREVIOUS_PATH="${DEPLOY_PATH}-previous"
resolved_deploy_path=$(readlink -m -- "$DEPLOY_PATH")
[ "$resolved_deploy_path" = "$DEPLOY_PATH" ] || { echo "DEPLOY_PATH must be normalized" >&2; exit 64; }
case "$DEPLOY_PATH" in /opt/*) ;; *) echo "unsafe DEPLOY_PATH" >&2; exit 64 ;; esac

restore_source() {
  if [ ! -d "$PREVIOUS_PATH" ]; then return; fi
  local failed_path="${DEPLOY_PATH}-rolled-back-$(date -u +%Y%m%dT%H%M%SZ)"
  mv "$DEPLOY_PATH" "$failed_path"
  mv "$PREVIOUS_PATH" "$DEPLOY_PATH"
  COMPOSE="$DEPLOY_PATH/deploy/resource-server/compose.production.yml"
}

restore_container() {
  local name=$1
  local backup="${name}-pre-workspace"
  if ! docker inspect "$backup" >/dev/null 2>&1; then
    echo "No rollback container for $name" >&2
    return
  fi
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker rename "$backup" "$name"
  docker start "$name" >/dev/null
}

restore_image() {
  local service=$1 current=$2 previous=$3
  if ! docker image inspect "$previous" >/dev/null 2>&1; then
    echo "No previous image for $service" >&2
    return
  fi
  docker tag "$previous" "$current"
  docker compose -f "$COMPOSE" up -d --no-deps --force-recreate "$service"
}

case "$COMPONENT" in
  docs)
    restore_source
    if docker inspect mozhi-agent-workspace-docs-pre-workspace >/dev/null 2>&1; then restore_container mozhi-agent-workspace-docs; else restore_image docs mozhi-agent-workspace-docs:local mozhi-agent-workspace-docs:previous; fi
    ;;
  edge)
    restore_source
    if docker inspect mozhi-agent-service-edge-pre-workspace >/dev/null 2>&1; then restore_container mozhi-agent-service-edge; else restore_image edge mozhi-agent-service-edge:local mozhi-agent-service-edge:previous; fi
    ;;
  ccn) restore_source; restore_image ccn-api ccn-brief-task-api:local ccn-brief-task-api:previous ;;
  all)
    restore_source
    restore_image ccn-api ccn-brief-task-api:local ccn-brief-task-api:previous
    if docker inspect mozhi-agent-workspace-docs-pre-workspace >/dev/null 2>&1; then restore_container mozhi-agent-workspace-docs; else restore_image docs mozhi-agent-workspace-docs:local mozhi-agent-workspace-docs:previous; fi
    if docker inspect mozhi-agent-service-edge-pre-workspace >/dev/null 2>&1; then restore_container mozhi-agent-service-edge; else restore_image edge mozhi-agent-service-edge:local mozhi-agent-service-edge:previous; fi
    ;;
  *) echo "invalid COMPONENT=$COMPONENT" >&2; exit 64 ;;
esac
