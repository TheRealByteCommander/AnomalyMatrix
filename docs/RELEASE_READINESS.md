# AnomalyMatrix — Release Readiness Checklist

Stand: **v1.0.0** (Production-hardened)

## Build & Tests

| Check | Status |
|-------|--------|
| Backend pytest (52+ Tests inkl. Security) | ✅ |
| Performance gate < 500 ms | ✅ |
| Parallel load smoke (10 runs) | ✅ |
| Production guard + hardening tests | ✅ |
| Frontend build + Playwright E2E | ✅ |
| CI: backend + frontend + e2e + prod + `pip-audit`/`npm audit` | ✅ |
| Dependabot (pip/npm/actions) | ✅ |

## Security

| Check | Status |
|-------|--------|
| RBAC enforced in prod | ✅ |
| JWT + Secure HttpOnly Session cookie | ✅ |
| No JWT persistence in `localStorage` | ✅ |
| CORS allowlist (`AMX_CORS_ORIGINS`) | ✅ |
| Rate limiting (+ login 10/min) | ✅ |
| Security headers (HSTS in prod) | ✅ |
| No dev-header auth in prod | ✅ |
| Unknown roles rejected (no admin escalation) | ✅ |
| Edge + OPC-UA HTTP service token | ✅ |
| `/license/status` + `/contracts/*` authenticated | ✅ |
| License admin dual-control token | ✅ |
| No exception leakage in prod 500s | ✅ |
| OPC-UA Sign/Encrypt (env-gated) | ✅ |
| Secrets via `.env.production` (gitignored) | ✅ |
| `file://` frame reads path-restricted | ✅ |

## Production Stack

| Check | Status |
|-------|--------|
| `docker-compose.prod.yml` (no public data ports) | ✅ |
| Frontend nginx + API proxy | ✅ |
| HMI login (`VITE_REQUIRE_AUTH`) | ✅ |
| Postgres pooling + composite index (`005`) | ✅ |
| Async Influx metrics writer | ✅ |
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
