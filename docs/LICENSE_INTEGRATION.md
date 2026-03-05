# License Integration v1

Endpoints:
- `GET /api/v1/license/status`
- `POST /api/v1/license/activate`
- `POST /api/v1/license/deactivate`

Admin token header for mutable endpoints:
- `X-License-Admin-Token`

Offline grace:
- configurable via `LICENSE_OFFLINE_GRACE_HOURS`
- validation loop interval via `LICENSE_VALIDATE_INTERVAL_SEC`

Security note:
- MVP stores token in file (`LICENSE_STATE_FILE`).
- Upgrade to vault/KMS before production.
