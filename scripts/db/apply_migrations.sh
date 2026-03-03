#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=anomalymatrix}"
: "${POSTGRES_USER:=anomaly}"
: "${POSTGRES_PASSWORD:=anomaly_pw}"

export PGPASSWORD="$POSTGRES_PASSWORD"

for f in "$(dirname "$0")"/*.sql; do
  echo "Applying migration: $f"
  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f"
done

echo "Migrations applied."
