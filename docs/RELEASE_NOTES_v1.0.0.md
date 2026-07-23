# AnomalyMatrix v1.0.0 – Release Notes

**Datum:** 2026-07-23  
**Tag:** `v1.0.0`  
**Commit:** `master` (Production-hardened)

## Status

**Pilot- / kontrollierter OT-Deploy ready.**  
Für 24/7-Produktion zusätzlich: TLS vor dem HMI, Kunden-PKI für OPC-UA, Secret-Rotation (siehe Rollout-Gates).

## Highlights seit v0.1.0 / v0.8.0

### Production Hardening
- `SERVICE_AUTH_TOKEN` / `X-AMX-Service-Token` für API ↔ Edge ↔ OPC-UA
- RBAC: unbekannte Rollen werden abgelehnt (kein Admin-Escalation)
- JWT nur im Memory; Session-Cookie `HttpOnly` + `Secure` + `SameSite=Lax`
- Auth auf `/license/status` und `/contracts/*`
- Prod-Startup-Guards (`ANOMALYMATRIX_ENV=prod`) inkl. Seed-Secret-Ablehnung
- Kein Exception-Leakage in Prod-500s; Login-Rate-Limit
- Edge-Capture in Prod **fail-closed** (kein stilles Synthetic-Fallback)

### Autonomer Linux-Installer
- Empfohlenes Host-OS: **Ubuntu Server 24.04 LTS**
- `scripts/install.sh` / `dist/AnomalyMatrix-installer-v1.0.0.run`
- Secrets, UFW, systemd, Compose Prod-Overlay, Lizenz-Bootstrap, Smoke-Inspektion
- `OPCUA_API_KEY` wird in Postgres (`users.api_key` / operator-1) synchronisiert; Seed-Keys werden rotiert

### OPC-UA & Line
- Contract-String-NodeIds (`ns=2;s=…`) statt numerischer Auto-IDs
- Sign/Encrypt in Prod (`OPCUA_SECURITY_ENABLED=true`)
- Busy-Reset bei API-/Capture-Fehlern

### Plattform
- Compose-Split: `docker-compose.yml` + `.dev.yml` / `.prod.yml`
- Postgres-Healthcheck vor API-Start; Connection-Pooling; Index `005`
- MinIO-Heatmaps über HMI-Pfad `/artifacts/` (`MINIO_PUBLIC_BASE`)
- Dependabot + CI `pip-audit` / `npm audit`
- Frontend: React 19, Vite 8, Playwright E2E

### Produkt / Docs
- Add-on-Sets Vertriebsdoku: `docs/product/ANOMALYMATRIX_ADDON_SETS_VERTIEB.md`
- Runbook: `docs/PRODUCTION_RUNBOOK.md`
- Freigabe: `docs/RELEASE_READINESS.md`

## Install

### Frisches Ubuntu Server 24.04 LTS

```bash
# Variante A — One-liner (aktueller master)
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/v1.0.0/scripts/install.sh \
  | sudo bash -s -- --host <SERVER-IP>

# Variante B — Release-Asset
sudo ./AnomalyMatrix-installer-v1.0.0.run --host <SERVER-IP>

# Mit TLS-Terminierung / Secure Cookies
sudo ./AnomalyMatrix-installer-v1.0.0.run --host <SERVER-IP> --tls
```

### Bestehende Installation (Compose)

```bash
git fetch origin tag v1.0.0
git checkout v1.0.0
cp -n .env.production.example .env.production   # Secrets prüfen/ersetzen
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production up -d --build
```

Credentials nach Install: `/opt/anomalymatrix/CREDENTIALS.txt` (Pfad je nach Installer-Ziel).

## Rollout-Gates (vor 24/7)

| Gate | Aktion |
|------|--------|
| TLS | Reverse-Proxy / `--tls`; `COOKIE_SECURE=true` |
| OPC-UA PKI | Self-Signed durch Kunden-Zertifikate ersetzen |
| Secrets | Alle `REPLACE_*` / generierten Secrets ins Vault; Seed-API-Keys nicht belassen |
| Kamera | `CAMERA_DRIVER=opencv` + reale Quelle (Default Install: synthetic) |
| Monitoring | Influx/Observability-Summary an Betriebs-Monitoring anbinden |

## Explizit nicht in v1.0.0

- GigE / GenICam Industriekameras (OpenCV-Webcam/Datei ist enthalten)
- WebSocket Live-View
- CI-Image-Builds für Gateway/Edge (Unit/E2E/Security-CI ist grün)

## Verifikation (CI / lokal)

```bash
# Backend (Provider-Matrix)
cd backend
ANOMALYMATRIX_INFERENCE_PROVIDER=stub pytest -q
ANOMALYMATRIX_INFERENCE_PROVIDER=opencv_ready pytest -q
ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore pytest -q

# Production guards
pytest -q tests/test_production_guards.py tests/test_security_hardening.py tests/test_post_merge_hardening.py

# Frontend
cd frontend && npm ci --legacy-peer-deps && npm run smoke && npm run test:e2e
```

## Upgrade-Hinweis von v0.8.x

1. `.env.production` um `SERVICE_AUTH_TOKEN`, `OPCUA_API_KEY`, `MINIO_PUBLIC_BASE=/artifacts` ergänzen  
2. Compose auf Split-Dateien umstellen (`docker-compose.yml` + `docker-compose.prod.yml`)  
3. DB-Migration `005_perf_indexes.sql` anwenden (frische Installs laden `001`–`005` automatisch)  
4. Stack neu bauen: `up -d --build`  
5. Admin-Login + eine Smoke-Inspektion

## Assets

| Datei | Beschreibung |
|-------|--------------|
| `AnomalyMatrix-installer-v1.0.0.run` | Self-extracting Installer |
| `AnomalyMatrix-installer.run` | Alias (gleiche Bytes) |
| `SHA256SUMS.txt` | Prüfsummen der Installer |

Installer lokal bauen:

```bash
./scripts/build_installer.sh
```
