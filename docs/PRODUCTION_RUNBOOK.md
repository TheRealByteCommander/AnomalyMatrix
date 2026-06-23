# AnomalyMatrix v1.0.0 — Production Runbook

## Pre-Deploy Checklist

1. Copy `.env.production.example` → `.env.production` and replace **all** `REPLACE_*` secrets
2. Set `AMX_CORS_ORIGINS` to your HMI URL (HTTPS)
3. Set `AMX_ADMIN_PASSWORD` for first admin login
4. Rotate API keys in Postgres (`users.api_key`) — do not use seed keys
5. Run migrations: `./scripts/db/apply_migrations.sh`
6. Build installer (optional): `bash scripts/build_installer.sh`

## Deploy (Docker)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Services:
- HMI: port **80** (nginx → API proxy `/api/`)
- API: port **8080**
- OPC-UA: **4840** (Sign/Encrypt when `OPCUA_SECURITY_ENABLED=true`)

## Post-Deploy Smoke

```bash
curl -fsS http://localhost:8080/api/v1/health
curl -fsS -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"admin-1","password":"YOUR_ADMIN_PASSWORD"}'
```

HMI: open `/` → login → run inspection from Dashboard.

## Backup (daily)

```bash
POSTGRES_PASSWORD=... ./scripts/backup/backup.sh
```

Restore: `./scripts/backup/restore.sh backups/<timestamp>`

## Rollback Model (< 60s)

```bash
curl -X POST http://localhost:8080/api/v1/models/rollback \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring

- `GET /api/v1/observability/summary`
- `GET /api/v1/events/recent`
- Influx measurements: `inspection_metrics`, `process_trends`

## Security Notes

- `ANOMALYMATRIX_ENV=prod` enforces config validation at API startup
- Dev headers (`X-AMX-Role`) are **rejected** in production
- OPC-UA uses self-signed certs by default — replace with PKI for customer rollout
- Place TLS termination (reverse proxy) in front of nginx for HTTPS
