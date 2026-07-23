# AnomalyMatrix v1.0.0 — Production Runbook

## Pre-Deploy Checklist

1. Copy `.env.production.example` → `.env.production` and replace **all** `REPLACE_*` secrets
2. Generate strong values for:
   - `JWT_SECRET` (≥32 chars)
   - `SERVICE_AUTH_TOKEN` (≥24 chars) — shared by API ↔ edge ↔ OPC-UA gateway
   - `LICENSE_ADMIN_TOKEN`
   - `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`, `INFLUX_TOKEN`, `OPCUA_API_KEY`
3. Set `AMX_CORS_ORIGINS` to your HMI URL (HTTPS)
4. Set `AMX_ADMIN_PASSWORD` for first admin login
5. Rotate API keys in Postgres (`users.api_key`) — **do not** use seed keys (`amx-key-*`)
6. Run migrations: `./scripts/db/apply_migrations.sh`
7. Place TLS termination (reverse proxy / load balancer) in front of nginx; keep `COOKIE_SECURE=true`

## Deploy (Docker)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Oder autonom vom frischen Ubuntu Server 24.04 LTS:

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
  | sudo bash -s -- --host <SERVER-IP>
```

Services (production overlay):
- HMI: port **80** (nginx → API proxy `/api/`)
- API: **127.0.0.1:8080** only (not public)
- Edge / MinIO / Postgres / Influx: **no host ports** (Docker network only)
- OPC-UA PLC: **4840** (Sign/Encrypt when `OPCUA_SECURITY_ENABLED=true`)
- Edge & OPC-UA HTTP require header `X-AMX-Service-Token: $SERVICE_AUTH_TOKEN`

## Post-Deploy Smoke

```bash
curl -fsS http://127.0.0.1:8080/api/v1/health
curl -fsS -c /tmp/amx.cookie -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"admin-1","password":"YOUR_ADMIN_PASSWORD"}'
curl -fsS -b /tmp/amx.cookie http://127.0.0.1:8080/api/v1/auth/me
```

HMI: open `/` → login → run inspection from Dashboard.

## Backup (daily)

```bash
POSTGRES_PASSWORD=... ./scripts/backup/backup.sh
```

Restore: `./scripts/backup/restore.sh backups/<timestamp>`

## Rollback Model (< 60s)

```bash
curl -X POST http://127.0.0.1:8080/api/v1/models/rollback \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring

- `GET /api/v1/observability/summary` (authenticated)
- `GET /api/v1/events/recent` (authenticated)
- Influx measurements: `inspection_metrics`, `process_trends` (async writer)

## Security Notes

- `ANOMALYMATRIX_ENV=prod` enforces config validation at API startup (incl. `SERVICE_AUTH_TOKEN`)
- Dev headers (`X-AMX-Role`) are **rejected** in production; unknown roles never escalate to admin
- Session cookie is `HttpOnly` + `Secure` + `SameSite=Lax`; JWTs are not stored in `localStorage`
- `/license/status` and `/contracts/*` require authentication
- License activate/deactivate require RBAC **and** `X-License-Admin-Token`
- Login is rate-limited (10 req/min/IP)
- 500 responses never leak exception strings in production
- OPC-UA uses self-signed certs by default — replace with customer PKI for rollout
- Dependabot is enabled (`.github/dependabot.yml`); CI runs `pip-audit` and `npm audit`
