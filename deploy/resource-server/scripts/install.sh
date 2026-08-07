#!/usr/bin/env bash
set -euo pipefail

SOURCE=${1:?usage: install.sh <extracted-source-root>}
DEPLOY_PATH=${DEPLOY_PATH:-/opt/mozhi-agent-workspace-services}
COMPONENT=${COMPONENT:-all}
SKIP_IMAGE_BUILD=${SKIP_IMAGE_BUILD:-false}
COMPOSE="$DEPLOY_PATH/deploy/resource-server/compose.production.yml"
SECRET_ROOT=/etc/mozhi-agent-workspace
DATA_ROOT=/var/lib/mozhi-agent-workspace
PREVIOUS_PATH="${DEPLOY_PATH}-previous"

case "$DEPLOY_PATH" in
  /opt/*) ;;
  *) echo "DEPLOY_PATH must be a specific child of /opt: $DEPLOY_PATH" >&2; exit 64 ;;
esac
[ "$DEPLOY_PATH" != "/opt/" ] && [ "$DEPLOY_PATH" != "/opt" ] || { echo "unsafe DEPLOY_PATH" >&2; exit 64; }
resolved_deploy_path=$(readlink -m -- "$DEPLOY_PATH")
[ "$resolved_deploy_path" = "$DEPLOY_PATH" ] || { echo "DEPLOY_PATH must be normalized" >&2; exit 64; }

case "$COMPONENT" in docs|ccn|edge|all) ;; *) echo "invalid COMPONENT=$COMPONENT" >&2; exit 64 ;; esac
case "$SKIP_IMAGE_BUILD" in true|false) ;; *) echo "invalid SKIP_IMAGE_BUILD=$SKIP_IMAGE_BUILD" >&2; exit 64 ;; esac
test -f "$SOURCE/deploy/resource-server/compose.production.yml"
mkdir -p "$(dirname "$DEPLOY_PATH")" "$SECRET_ROOT" "$DATA_ROOT/ccn-postgres" "$DATA_ROOT/ccn-redis" /var/backups/mozhi-agent-workspace/ccn-brief-report
chmod 700 "$SECRET_ROOT" "$DATA_ROOT/ccn-postgres" "$DATA_ROOT/ccn-redis"
chown 70:70 "$DATA_ROOT/ccn-postgres"
chown 999:1000 "$DATA_ROOT/ccn-redis"

random_hex() { openssl rand -hex "$1"; }

ensure_ccn_env() {
  local env_file="$SECRET_ROOT/ccn-api.env"
  [ -f "$env_file" ] && return
  local pg_password redis_password api_key
  pg_password=$(random_hex 32)
  redis_password=$(random_hex 32)
  api_key=$(random_hex 32)
  umask 077
  cat > "$env_file" <<EOF
POSTGRES_DB=ccn
POSTGRES_USER=ccn
POSTGRES_PASSWORD=$pg_password
DATABASE_URL=postgresql+psycopg://ccn:$pg_password@postgres:5432/ccn
REDIS_PASSWORD=$redis_password
REDIS_URL=redis://:$redis_password@redis:6379/0
CCN_API_KEY=$api_key
ENABLE_API_DOCS=false
AUTH_FAIL_LIMIT_PER_MINUTE=10
READ_LIMIT_PER_MINUTE=120
WRITE_LIMIT_PER_MINUTE=30
EOF
  echo "Created $env_file with generated secrets; values were not printed." >&2
}

migrate_legacy_ccn_api_keys() {
  local env_file="$SECRET_ROOT/ccn-api.env"
  grep -q '^CCN_API_KEY=' "$env_file" && return

  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
  local legacy_keys="${CCN_OPERATOR_API_KEYS:-${CCN_WORKER_API_KEYS:-${CCN_PRODUCER_API_KEYS:-}}}"
  local api_key="${legacy_keys%%,*}"
  [ -n "$api_key" ] || { echo "Cannot migrate legacy CCN API keys." >&2; exit 1; }

  local replacement
  replacement=$(mktemp "$SECRET_ROOT/ccn-api.env.XXXXXX")
  awk '!/^CCN_(PRODUCER|WORKER|OPERATOR)_API_KEYS=/' "$env_file" > "$replacement"
  printf 'CCN_API_KEY=%s\n' "$api_key" >> "$replacement"
  chmod 600 "$replacement"
  mv "$replacement" "$env_file"
  unset CCN_PRODUCER_API_KEYS CCN_WORKER_API_KEYS CCN_OPERATOR_API_KEYS legacy_keys api_key
  echo "Migrated CCN authentication to one API key; value was not printed." >&2
}

ensure_edge_env() {
  local env_file="$SECRET_ROOT/edge.env"
  [ -f "$env_file" ] && return
  if [ -f /etc/red-flower-garden/edge.env ]; then
    set -a
    # shellcheck disable=SC1091
    . /etc/red-flower-garden/edge.env
    set +a
  fi
  if [ -z "${FRP_TOKEN:-}" ] && docker inspect mozhi-agent-service-edge >/dev/null 2>&1; then
    FRP_TOKEN=$(docker inspect mozhi-agent-service-edge --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^FRP_TOKEN=//p' | head -n 1)
  fi
  if [ -z "${FRP_TOKEN:-}" ]; then
    echo "Cannot migrate FRP_TOKEN; create $env_file from config/edge.env.example." >&2
    exit 1
  fi
  umask 077
  cat > "$env_file" <<EOF
FRP_TOKEN=$FRP_TOKEN
FRP_BIND_PORT=${FRP_BIND_PORT:-7000}
HEALTH_PROXY_PORT=${HEALTH_PROXY_PORT:-18081}
DESKTOP_API_PROXY_PORT=${DESKTOP_API_PROXY_PORT:-18081}
AGENT_HTTPS_SITE_ADDRESS=${CADDY_HTTPS_SITE_ADDRESS:-https://39.105.78.135}
AGENT_TLS_DIRECTIVE=tls internal
RED_FLOWER_API_DOMAIN=api.haohaoxiaoyu.top
RED_FLOWER_API_UPSTREAM=red-flower-garden-api:3000
DOCS_DOMAIN=docs.haohaoxiaoyu.top
DOCS_UPSTREAM=mozhi-agent-workspace-docs:8080
CCN_API_DOMAIN=ccn-api.haohaoxiaoyu.top
CCN_API_UPSTREAM=ccn-brief-task-api:8000
API_MAX_BODY_SIZE=1MB
EOF
  echo "Created $env_file by migrating the existing edge secret; values were not printed." >&2
}

adopt_existing_container() {
  local name=$1
  if ! docker inspect "$name" >/dev/null 2>&1; then return; fi
  local project
  project=$(docker inspect "$name" --format '{{index .Config.Labels "com.docker.compose.project"}}' 2>/dev/null || true)
  if [ "$project" = "mozhi-resource-server" ]; then return; fi
  local backup="${name}-pre-workspace"
  docker rm -f "$backup" >/dev/null 2>&1 || true
  docker rename "$name" "$backup"
  docker stop "$backup" >/dev/null
}

rollback_adopted() {
  for name in mozhi-agent-service-edge mozhi-agent-workspace-docs; do
    local backup="${name}-pre-workspace"
    if docker inspect "$backup" >/dev/null 2>&1; then
      docker rm -f "$name" >/dev/null 2>&1 || true
      docker rename "$backup" "$name"
      docker start "$name" >/dev/null
    fi
  done
  if [ -d "$PREVIOUS_PATH" ]; then
    local failed_path="${DEPLOY_PATH}-failed-$(date -u +%Y%m%dT%H%M%SZ)"
    mv "$DEPLOY_PATH" "$failed_path" >/dev/null 2>&1 || true
    mv "$PREVIOUS_PATH" "$DEPLOY_PATH"
  fi
}
finish_install() {
  local rc=$?
  trap - EXIT INT TERM
  if [ "$rc" -ne 0 ]; then
    echo "Deployment failed; restoring previous source and adopted containers." >&2
    set +e
    rollback_adopted
    set -e
  fi
  exit "$rc"
}
trap finish_install EXIT
trap 'exit 130' INT TERM

if [ -d "$DEPLOY_PATH" ]; then
  rm -rf "$PREVIOUS_PATH"
  mv "$DEPLOY_PATH" "$PREVIOUS_PATH"
fi
mv "$SOURCE" "$DEPLOY_PATH"
cd "$DEPLOY_PATH"

build_or_verify_image() {
  local service=$1 image=$2
  if [ "$SKIP_IMAGE_BUILD" = true ]; then
    docker image inspect "$image" >/dev/null 2>&1 || {
      echo "Preloaded image is missing: $image" >&2
      return 1
    }
    echo "Using preloaded image: $image" >&2
  else
    docker compose -f "$COMPOSE" build "$service"
  fi
}

ensure_ccn_env
migrate_legacy_ccn_api_keys
ensure_edge_env
docker volume create mozhi-caddy-data >/dev/null
docker network create mozhi-agent-services-edge >/dev/null 2>&1 || true
if docker inspect red-flower-garden-api >/dev/null 2>&1; then
  docker network connect mozhi-agent-services-edge red-flower-garden-api >/dev/null 2>&1 || true
fi

if [ "$COMPONENT" = docs ] || [ "$COMPONENT" = all ]; then
  adopt_existing_container mozhi-agent-workspace-docs
  if docker image inspect mozhi-agent-workspace-docs:local >/dev/null 2>&1; then
    docker tag mozhi-agent-workspace-docs:local mozhi-agent-workspace-docs:previous
  fi
  build_or_verify_image docs mozhi-agent-workspace-docs:local
  docker compose -f "$COMPOSE" up -d --no-deps docs
fi

if [ "$COMPONENT" = ccn ] || [ "$COMPONENT" = all ]; then
  docker compose -f "$COMPOSE" up -d postgres redis
  if docker image inspect ccn-brief-task-api:local >/dev/null 2>&1; then
    docker tag ccn-brief-task-api:local ccn-brief-task-api:previous
  fi
  build_or_verify_image ccn-api ccn-brief-task-api:local
  docker compose -f "$COMPOSE" run --rm --no-deps ccn-api alembic upgrade head
  docker compose -f "$COMPOSE" up -d --no-deps ccn-api
fi

if [ "$COMPONENT" = edge ] || [ "$COMPONENT" = all ]; then
  adopt_existing_container mozhi-agent-service-edge
  if docker image inspect mozhi-agent-service-edge:local >/dev/null 2>&1; then
    docker tag mozhi-agent-service-edge:local mozhi-agent-service-edge:previous
  fi
  build_or_verify_image edge mozhi-agent-service-edge:local
  docker compose -f "$COMPOSE" up -d --no-deps edge
  for attempt in $(seq 1 60); do
    if curl -kfsS https://127.0.0.1/health >/dev/null \
      && curl -fsS --resolve api.haohaoxiaoyu.top:443:127.0.0.1 https://api.haohaoxiaoyu.top/health >/dev/null \
      && curl -fsS --resolve docs.haohaoxiaoyu.top:443:127.0.0.1 https://docs.haohaoxiaoyu.top/healthz >/dev/null \
      && [ "$(docker inspect ccn-brief-task-api --format '{{.State.Health.Status}}')" = healthy ]; then
      break
    fi
    if [ "$attempt" -eq 60 ]; then
      docker logs --tail 120 mozhi-agent-service-edge >&2 || true
      echo "Unified edge routes did not become healthy." >&2
      exit 1
    fi
    sleep 2
  done
fi

python3 deploy/resource-server/scripts/smoke-test.py --internal --skip-write
trap - EXIT INT TERM
echo "Deployment succeeded: component=$COMPONENT path=$DEPLOY_PATH"
