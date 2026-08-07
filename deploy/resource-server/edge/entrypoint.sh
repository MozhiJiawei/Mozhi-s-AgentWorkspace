#!/usr/bin/env bash
set -euo pipefail

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 64
  fi
}

require_env FRP_TOKEN
export FRP_BIND_PORT="${FRP_BIND_PORT:-7000}"
export HEALTH_PROXY_PORT="${HEALTH_PROXY_PORT:-18081}"
export DESKTOP_API_PROXY_PORT="${DESKTOP_API_PROXY_PORT:-${HEALTH_PROXY_PORT}}"
export AGENT_HTTPS_SITE_ADDRESS="${AGENT_HTTPS_SITE_ADDRESS:-https://39.105.78.135}"
export AGENT_TLS_DIRECTIVE="${AGENT_TLS_DIRECTIVE:-tls internal}"
export RED_FLOWER_API_DOMAIN="${RED_FLOWER_API_DOMAIN:-api.haohaoxiaoyu.top}"
export RED_FLOWER_API_UPSTREAM="${RED_FLOWER_API_UPSTREAM:-red-flower-garden-api:3000}"
export DOCS_DOMAIN="${DOCS_DOMAIN:-docs.haohaoxiaoyu.top}"
export DOCS_UPSTREAM="${DOCS_UPSTREAM:-mozhi-agent-workspace-docs:8080}"
export CCN_API_DOMAIN="${CCN_API_DOMAIN:-ccn-api.haohaoxiaoyu.top}"
export CCN_API_UPSTREAM="${CCN_API_UPSTREAM:-ccn-brief-task-api:8000}"
export API_MAX_BODY_SIZE="${API_MAX_BODY_SIZE:-1MB}"

envsubst '${AGENT_HTTPS_SITE_ADDRESS} ${AGENT_TLS_DIRECTIVE} ${HEALTH_PROXY_PORT} ${DESKTOP_API_PROXY_PORT} ${RED_FLOWER_API_DOMAIN} ${RED_FLOWER_API_UPSTREAM} ${DOCS_DOMAIN} ${DOCS_UPSTREAM} ${CCN_API_DOMAIN} ${CCN_API_UPSTREAM} ${API_MAX_BODY_SIZE}' \
  < /etc/mozhi-edge/templates/Caddyfile.template \
  > /etc/mozhi-edge/generated/Caddyfile

cat > /etc/mozhi-edge/generated/frps.toml <<EOF
bindPort = ${FRP_BIND_PORT}
auth.method = "token"
auth.token = "${FRP_TOKEN}"
EOF

caddy validate --config /etc/mozhi-edge/generated/Caddyfile --adapter caddyfile
frps -c /etc/mozhi-edge/generated/frps.toml &
frps_pid="$!"
caddy run --config /etc/mozhi-edge/generated/Caddyfile --adapter caddyfile &
caddy_pid="$!"

terminate() {
  kill -TERM "$caddy_pid" "$frps_pid" 2>/dev/null || true
  wait "$caddy_pid" "$frps_pid" 2>/dev/null || true
}
trap terminate TERM INT
while kill -0 "$frps_pid" 2>/dev/null && kill -0 "$caddy_pid" 2>/dev/null; do sleep 2; done
terminate
exit 1
