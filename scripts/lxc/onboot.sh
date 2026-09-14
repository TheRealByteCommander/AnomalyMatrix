#!/usr/bin/env bash
# LXC / IPC on-boot: bring AnomalyMatrix back after host reboot.
# Install: copy to /etc/rc.local.d/ or enable scripts/systemd/anomalymatrix.service
set -euo pipefail
ROOT="${AMX_ROOT:-/opt/anomalymatrix}"
cd "$ROOT"
if [[ -f .env.production ]]; then
  docker compose -p anomalymatrix -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production up -d
else
  docker compose -p anomalymatrix -f docker-compose.yml up -d
fi
# Readiness self-test (API bound to localhost in prod)
sleep 8
curl -fsS http://127.0.0.1:8080/api/v1/health >/dev/null
curl -fsS http://127.0.0.1:8080/api/v1/ready >/dev/null || true
