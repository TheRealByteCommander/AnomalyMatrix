# AnomalyMatrix — Release Readiness Checklist

Stand: **v1.0.0** (Production)

## Build & Tests

| Check | Status |
|-------|--------|
| Backend pytest (45+ Tests) | ✅ |
| Performance gate < 500 ms | ✅ |
| Parallel load smoke (10 runs) | ✅ |
| Production guard tests | ✅ |
| Frontend build + Playwright E2E | ✅ |
| CI: backend + frontend + e2e + prod job | ✅ |

## Security

| Check | Status |
|-------|--------|
| RBAC enforced in prod | ✅ |
| JWT + Session auth | ✅ |
| CORS allowlist (`AMX_CORS_ORIGINS`) | ✅ |
| Rate limiting | ✅ |
| Security headers (HSTS in prod) | ✅ |
| No dev-header auth in prod | ✅ |
| OPC-UA Sign/Encrypt (env-gated) | ✅ |
| Secrets via `.env.production` | ✅ |

## Production Stack

| Check | Status |
|-------|--------|
| `docker-compose.prod.yml` | ✅ |
| Frontend nginx + API proxy | ✅ |
| HMI login (`VITE_REQUIRE_AUTH`) | ✅ |
| Postgres migrations incl. 004 | ✅ |
| Backup/restore scripts | ✅ |
| `docs/PRODUCTION_RUNBOOK.md` | ✅ |

## ML / Line Integration

| Check | Status |
|-------|--------|
| Training from MinIO/local images | ✅ |
| Promotion gate (samples + non-synthetic in prod) | ✅ |
| Model rollback endpoint | ✅ |
| Heatmap PNG to MinIO | ✅ |
| Raw frame storage | ✅ |
| OpenCV camera driver | ✅ |
| GigE/GenICam industrial cameras | 🔜 optional upgrade |

## Freigabe

| Umgebung | Status |
|----------|--------|
| Development | ✅ |
| Staging / Pilot | ✅ mit `.env.production` |
| **Production (24/7)** | ✅ nach Checkliste + Secret-Rotation + PKI-OPC-UA |
