# Ops Runbook: Licensing

Stand: API **v0.6.0**

## Status
```bash
curl http://localhost:8080/api/v1/license/status
```

## Activate
```bash
curl -X POST http://localhost:8080/api/v1/license/activate \
  -H 'Content-Type: application/json' \
  -H 'X-License-Admin-Token: <token>' \
  -H 'X-AMX-Role: admin' \
  -d '{"license_key":"<key>"}'
```

Wenn `RBAC_ENFORCE=true`: zusätzlich gültiger `X-AMX-Api-Key` (admin) oder `X-AMX-Role: admin`.

## Deactivate
```bash
curl -X POST http://localhost:8080/api/v1/license/deactivate \
  -H 'X-License-Admin-Token: <token>' \
  -H 'X-AMX-Role: admin'
```

## ENV (Auszug)
| Variable | Zweck |
|----------|--------|
| `LICENSE_ENFORCE` | Feature-Gates strikt |
| `LICENSE_ADMIN_TOKEN` | Admin-Header-Validierung |
| `LICENSE_OFFLINE_GRACE_HOURS` | Offline-Toleranz |
| `LICENSE_VALIDATE_INTERVAL_SEC` | Hintergrund-Validierung |

## Troubleshooting
- **402 Payment Required** — `LICENSE_ENFORCE=true` ohne aktive Lizenz
- **403** — RBAC: fehlende `license.admin`-Permission
- **401** — falscher `X-License-Admin-Token`
