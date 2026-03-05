# Ops Runbook: Licensing

## Activate
curl -X POST http://localhost:8080/api/v1/license/activate \
  -H 'Content-Type: application/json' \
  -H 'X-License-Admin-Token: <token>' \
  -d '{"license_key":"<key>"}'

## Status
curl http://localhost:8080/api/v1/license/status

## Deactivate
curl -X POST http://localhost:8080/api/v1/license/deactivate \
  -H 'X-License-Admin-Token: <token>'
