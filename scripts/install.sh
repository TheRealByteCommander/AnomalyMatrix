#!/usr/bin/env bash
set -euo pipefail

APP_NAME="AnomalyMatrix"
APP_DIR_DEFAULT="/opt/anomalymatrix"
REPO_URL_DEFAULT="https://github.com/TheRealByteCommander/AnomalyMatrix.git"
BRANCH_DEFAULT="master"

APP_DIR="${APP_DIR:-$APP_DIR_DEFAULT}"
REPO_URL="${REPO_URL:-$REPO_URL_DEFAULT}"
BRANCH="${BRANCH:-$BRANCH_DEFAULT}"

log() { echo "[$APP_NAME] $*"; }
err() { echo "[$APP_NAME][ERROR] $*" >&2; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { err "Required command missing: $1"; exit 1; }
}

ensure_docker_compose() {
  if docker compose version >/dev/null 2>&1; then
    return 0
  fi
  err "'docker compose' is not available. Install Docker Compose v2 first."
  exit 1
}

install_repo() {
  if [[ -d "$APP_DIR/.git" ]]; then
    log "Updating existing repo in $APP_DIR"
    git -C "$APP_DIR" fetch origin
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
  else
    log "Cloning repo into $APP_DIR"
    mkdir -p "$(dirname "$APP_DIR")"
    git clone "$REPO_URL" "$APP_DIR"
    git -C "$APP_DIR" checkout "$BRANCH"
  fi
}

prepare_env() {
  if [[ ! -f "$APP_DIR/.env" ]]; then
    if [[ -f "$APP_DIR/.env.example" ]]; then
      cp "$APP_DIR/.env.example" "$APP_DIR/.env"
      log "Created .env from .env.example (please review secrets)."
    else
      err "Missing .env.example in repository."
      exit 1
    fi
  fi
}

start_stack() {
  log "Starting Docker stack..."
  docker compose -f "$APP_DIR/docker-compose.yml" --env-file "$APP_DIR/.env" up -d --build
}

run_migrations() {
  if [[ -x "$APP_DIR/scripts/db/apply_migrations.sh" ]]; then
    log "Applying DB migrations..."
    (cd "$APP_DIR" && ./scripts/db/apply_migrations.sh) || log "Migration script returned non-zero (continuing)."
  else
    log "No executable migration script found; skipping."
  fi
}

health_check() {
  local url="http://127.0.0.1:8080/api/v1/health"
  log "Checking API health at $url"
  for i in {1..20}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "Health check OK"
      return 0
    fi
    sleep 2
  done
  err "Health check failed after retries."
  return 1
}

main() {
  require_cmd git
  require_cmd docker
  require_cmd curl
  ensure_docker_compose

  install_repo
  prepare_env
  start_stack
  run_migrations
  health_check || true

  cat <<EOF

$APP_NAME installation complete.

Project directory: $APP_DIR
API health:        http://127.0.0.1:8080/api/v1/health
MinIO console:     http://127.0.0.1:9001
InfluxDB:          http://127.0.0.1:8086

Useful commands:
  docker compose -f $APP_DIR/docker-compose.yml --env-file $APP_DIR/.env ps
  docker compose -f $APP_DIR/docker-compose.yml --env-file $APP_DIR/.env logs -f api
  docker compose -f $APP_DIR/docker-compose.yml --env-file $APP_DIR/.env down

EOF
}

main "$@"
