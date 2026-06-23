#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup-directory>" >&2
  exit 1
fi

SRC="$1"
: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=anomalymatrix}"
: "${POSTGRES_USER:=anomaly}"
: "${POSTGRES_PASSWORD:=anomaly_pw}"

export PGPASSWORD="$POSTGRES_PASSWORD"
pg_restore -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists "$SRC/postgres.dump"

if [[ -f "$SRC/backend-data.tgz" ]]; then
  tar -xzf "$SRC/backend-data.tgz" -C "$(dirname "$0")/../.."
fi

echo "[restore] Completed from $SRC"
