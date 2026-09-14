#!/usr/bin/env bash
# Post-reboot / commissioning self-test against the local API.
set -euo pipefail
BASE="${AMX_API:-http://127.0.0.1:8080/api/v1}"
curl -fsS "$BASE/health"
echo
curl -fsS "$BASE/ready" || true
echo
echo "Self-test endpoint requires auth; use HMI or:"
echo "  curl -b cookie -X POST $BASE/system/self-test"
