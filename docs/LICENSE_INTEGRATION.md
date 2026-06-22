# License Integration v1

Stand: API **v0.6.0** (unveränderte License-Endpunkte, RBAC auf Admin-Aktionen)

## Endpoints
- `GET /api/v1/license/status` — öffentlich lesbar (ohne RBAC)
- `POST /api/v1/license/activate` — Admin
- `POST /api/v1/license/deactivate` — Admin

## Auth
**License-Admin-Token** (weiterhin erforderlich):
- Header `X-License-Admin-Token`

**RBAC** (wenn `RBAC_ENFORCE=true`):
- Permission `license.admin`
- Rolle `admin` oder API-Key `amx-key-admin`

## Feature-Gating
`LICENSE_ENFORCE=true` blockiert u. a.:
- `inspection.run`
- `inspection.read` (über `_guard` → License-Feature-Mapping)

## Offline / Grace
- `LICENSE_OFFLINE_GRACE_HOURS` (Default 24)
- `LICENSE_VALIDATE_INTERVAL_SEC` (Default 60)
- Status in `GET /license/status`: `grace_active`, `active`, `tier`

## Persistenz
- `LICENSE_STATE_FILE` (Default `backend/data/license_state.json`)

## Security note
- MVP speichert Token in Datei — vor Produktion Vault/KMS.
- `LICENSE_ADMIN_TOKEN` nur serverseitig, nie im Frontend.

Siehe auch `docs/OPS_LICENSE_RUNBOOK.md`.
