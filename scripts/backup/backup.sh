#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${BACKUP_DIR:-$ROOT/backups}/$STAMP"
mkdir -p "$DEST"

: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=anomalymatrix}"
: "${POSTGRES_USER:=anomaly}"
: "${POSTGRES_PASSWORD:=anomaly_pw}"

echo "[backup] Writing to $DEST"
export PGPASSWORD="$POSTGRES_PASSWORD"
pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "$DEST/postgres.dump"

if command -v mc >/dev/null 2>&1 && [[ -n "${MINIO_ENDPOINT:-}" ]]; then
  mc mirror "local/raw-images" "$DEST/minio-raw-images" || true
  mc mirror "local/heatmaps" "$DEST/minio-heatmaps" || true
fi

tar -czf "$DEST/backend-data.tgz" -C "$ROOT/backend" data 2>/dev/null || true
echo "[backup] Complete: $DEST"
