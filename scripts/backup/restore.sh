#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup-directory>" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$1"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-anomalymatrix}"
MODE="${MODE:-prod}"

compose() {
  if [[ "$MODE" == "prod" ]]; then
    docker compose -p "$COMPOSE_PROJECT" \
      -f "$ROOT/docker-compose.yml" \
      -f "$ROOT/docker-compose.prod.yml" \
      --env-file "${ENV_FILE:-$ROOT/.env.production}" \
      "$@"
  else
    docker compose -p "$COMPOSE_PROJECT" \
      -f "$ROOT/docker-compose.yml" \
      -f "$ROOT/docker-compose.dev.yml" \
      --env-file "${ENV_FILE:-$ROOT/.env}" \
      "$@"
  fi
}

if compose ps --status running postgres >/dev/null 2>&1; then
  compose exec -T postgres pg_restore -U anomaly -d anomalymatrix --clean --if-exists < "$SRC/postgres.dump"
else
  : "${POSTGRES_HOST:=localhost}"
  : "${POSTGRES_PORT:=5432}"
  : "${POSTGRES_DB:=anomalymatrix}"
  : "${POSTGRES_USER:=anomaly}"
  : "${POSTGRES_PASSWORD:=anomaly_pw}"
  export PGPASSWORD="$POSTGRES_PASSWORD"
  pg_restore -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists "$SRC/postgres.dump"
fi

if [[ -f "$SRC/backend-data.tgz" ]]; then
  tar -xzf "$SRC/backend-data.tgz" -C "$ROOT"
fi

echo "[restore] Completed from $SRC"
