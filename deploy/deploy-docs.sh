#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/mozhi-agent-workspace-docs}
REPO_URL=${REPO_URL:-https://github.com/MozhiJiawei/Mozhi-s-AgentWorkspace.git}
BRANCH=${BRANCH:-main}
DOCS_PORT=${DOCS_PORT:-8080}
NODE_IMAGE=${NODE_IMAGE:-node:24.13.1-alpine3.22}
FORCE_REBUILD=${FORCE_REBUILD:-0}

ensure_compose() {
  if docker compose version >/dev/null 2>&1; then
    return
  fi

  apt-get update
  apt-get install -y docker-compose-plugin

  if ! docker compose version >/dev/null 2>&1; then
    echo "docker compose is still unavailable after installing docker-compose-plugin" >&2
    exit 1
  fi
}

ensure_checkout() {
  if [ ! -d "$APP_DIR/.git" ]; then
    mkdir -p "$(dirname "$APP_DIR")"
    git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  fi

  cd "$APP_DIR"
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
  git submodule sync --recursive
  git submodule update --init --recursive
}

deploy_docs() {
  cd "$APP_DIR"

  if [ "$FORCE_REBUILD" = "1" ] || ! docker image inspect mozhi-agent-workspace-docs:local >/dev/null 2>&1; then
    DOCS_PORT="$DOCS_PORT" NODE_IMAGE="$NODE_IMAGE" docker compose -f compose.docs.yml build docs
  fi

  DOCS_PORT="$DOCS_PORT" NODE_IMAGE="$NODE_IMAGE" docker compose -f compose.docs.yml up -d --no-build docs
  DOCS_PORT="$DOCS_PORT" docker compose -f compose.docs.yml restart docs
}

verify_docs() {
  for _ in $(seq 1 20); do
    if curl -fsS "http://127.0.0.1:$DOCS_PORT/healthz" >/dev/null; then
      docker ps --filter "name=mozhi-agent-workspace-docs" \
        --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
      curl -fsS "http://127.0.0.1:$DOCS_PORT/healthz"
      echo
      return
    fi
    sleep 1
  done

  docker logs --tail 120 mozhi-agent-workspace-docs 2>&1 || true
  echo "Docs service did not become healthy on port $DOCS_PORT" >&2
  exit 1
}

ensure_compose
ensure_checkout
deploy_docs
verify_docs
