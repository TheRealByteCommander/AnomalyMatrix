# AnomalyMatrix

Engineering-first MVP for industrial anomaly detection (unüberwachte Gut-Teil-Prüfung, Operator-HMI, OPC-UA-Anbindung).

**Aktueller Stand (2026-07):** API **v1.2.0** — Pilot-/Deploy-ready (siehe Rollout-Gates in `docs/RELEASE_READINESS.md`)  
**Installation:** `docs/INSTALLATION.md` · **Konfiguration:** `docs/CONFIGURATION.md` · **Multi-Kamera:** `docs/MULTI_CAMERA.md`  
**Deployment:** `docker-compose.prod.yml` + `.env.production` — siehe `docs/PRODUCTION_RUNBOOK.md`  
**GitHub Release:** `v1.2.0` — `docs/RELEASE_NOTES_v1.2.0.md`

## Ziele
- Unüberwachte Anomalieerkennung auf Gut-Teilen
- Continual-Learning Feedback-Loop (Human-in-the-Loop)
- OPC-UA Integration (Machine Vision Companion Spec)
- Tesla-inspiriertes, operator-first HMI
- Trendanalyse & Frühwarnungen für Prozessdrift

## Wofür wird AnomalyMatrix eingesetzt?

AnomalyMatrix ist eine **Inline-Qualitätslösung** für die Produktion: Sie prüft Bauteile an der Linie auf Abweichungen vom Gut-Teil, ohne jeden Fehlertyp vorab zu programmieren.

| Einsatz | Nutzen |
|---------|--------|
| **100-%-Kontrolle** | Jedes Teil nach kritischem Prozessschritt bewerten |
| **SPS-Integration** | Automatischer Trigger, Stop/Ausschleusen bei rot über OPC UA |
| **Operator-HMI** | Ampel, Score, letzte Inspektionen — schnelle Entscheidung am Band |
| **QA-Feedback** | Falschmeldungen markieren, echte Defekte dokumentieren |
| **Trends** | Prozessdrift früh erkennen — bei Multi-View **pro Kamera** |

Ausführliche Beschreibung (DE/EN): **Hilfe & FAQ** im HMI oder `docs/PRODUCT_APPLICATION.md`.

## Repository Layout
| Pfad | Inhalt |
|------|--------|
| `backend/` | FastAPI API (Inspection, RBAC, License, Observability) |
| `frontend/` | React/Vite HMI (Dashboard, Detail, Trends, Config) |
| `edge-acquisition/` | HTTP Capture + Kamera-Discovery (`GET /cameras`) |
| `opcua-gateway/` | HTTP `/publish` + asyncua OPC-UA-Server (Port 4840, Multi-View LastResult) |
| `infra/` | Infra-Manifeste (Platzhalter) |
| `scripts/` | DB-Migrationen, Installer, Automation |
| `tests/` | Top-Level Integration-Test-Workspace |
| `contracts/` | Versionierte JSON-Schemas (Envelope, Events, OPC-UA) |

## Schnellstart (lokal, Windows)

### Backend (Port 8080)
```powershell
cd backend
py -3 -m pip install -r requirements.txt
py -3 -m pytest -q
py -3 -m uvicorn app.main:app --reload --port 8080
```

### Frontend (Port 5173)
Node **18+** erforderlich (`winget install OpenJS.NodeJS.18` oder `OpenJS.NodeJS.20`).

```powershell
cd frontend
npm install
npm run dev
```

Browser: [http://localhost:5173](http://localhost:5173) — Dev-Server muss laufen (`ERR_CONNECTION_REFUSED` = `npm run dev` nicht gestartet).

API-Health: [http://127.0.0.1:8080/api/v1/health](http://127.0.0.1:8080/api/v1/health)

Details: `docs/INSTALLATION.md`

## Docker Compose (Development)
```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env up --build
```

## Production Deploy (autonom vom frischen OS)

**Empfohlenes Host-OS: Ubuntu Server 24.04 LTS**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
  | sudo bash -s -- --host <SERVER-IP>
```

Manuell:
```bash
cp .env.production.example .env.production   # secrets ersetzen
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Runbook: `docs/PRODUCTION_RUNBOOK.md` · Installation: `docs/INSTALLATION.md` · Konfiguration: `docs/CONFIGURATION.md` · Freigabe: `docs/RELEASE_READINESS.md`

| Service | Dev-Port | Prod |
|---------|----------|------|
| HMI (nginx) | — | **80** |
| API | 8080 | localhost:8080 |
| edge-acquisition | 8091 | internal + `X-AMX-Service-Token` |
| opcua-gateway (HTTP) | 8092 | internal + `X-AMX-Service-Token` |
| opcua-gateway (OPC-UA) | 4840 | 4840 |
| Postgres | 5432 | internal |
| InfluxDB | 8086 | internal |
| MinIO | 9000 / 9001 | internal |

DB-Init-Skripte werden aus `scripts/db/` in Postgres geladen (`001`–`005`).

## API v1.2.0 (Auszug)

### Auth & Training
- `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`
- `POST /api/v1/models/train`, `POST /api/v1/models/{id}/promote`, `POST /api/v1/models/rollback`

### Inspection & Ergebnisse
- `POST /api/v1/inspections/run` (Alias: `/orchestrate/run-inspection`) — optional `camera_ids` (1–4)
- `GET /api/v1/inspections/recent` (Alias: `/results/latest`)
- `GET /api/v1/results/query` — Filter `camera_id` (jede View)
- `GET /api/v1/results/trend-summary` — inkl. `by_camera` Drift
- `POST /api/v1/edge/capture`, `POST /api/v1/ai/infer`

### Kameras (Multi-View)
- `GET /api/v1/cameras` — Hardware-Erkennung + Auswahl
- `GET` / `PUT /api/v1/cameras/selection` — 1–4 Kameras speichern
- Details: `docs/MULTI_CAMERA.md`

### Catalog, Feedback, Audit
- `GET /api/v1/recipes`, `GET /api/v1/models`
- `POST /api/v1/feedback`, `GET /api/v1/feedback`
- `GET /api/v1/audit/recent`

### Observability & Events
- `GET /api/v1/observability/summary`
- `GET /api/v1/events/recent`
- `GET /api/v1/contracts/events`, `GET /api/v1/contracts/inspection-result`

### License
- `GET /api/v1/license/status`
- `POST /api/v1/license/activate`, `POST /api/v1/license/deactivate`

## Konfiguration (ENV, wichtigste)

| Variable | Zweck |
|----------|--------|
| `ANOMALYMATRIX_ENV` | `prod` = Startup-Guards, Auth-Pflicht, CORS, Rate-Limits |
| `SERVICE_AUTH_TOKEN` | Shared Token API ↔ Edge ↔ OPC-UA Gateway (Prod-Pflicht) |
| `AMX_CORS_ORIGINS` | Erlaubte HMI-Origins (Prod, kommagetrennt) |
| `AMX_ADMIN_PASSWORD` | Einmaliges Admin-Passwort-Bootstrap (Prod) |
| `COOKIE_SECURE` | Session-Cookie nur über HTTPS (Default in Prod: true) |
| `DATABASE_URL` | Postgres (Compose); leer = JSONL-Fallback |
| `ANOMALYMATRIX_INFERENCE_PROVIDER` | `stub` \| `opencv_ready` \| `patchcore` |
| `EDGE_ACQUISITION_URL` | Edge-Capture HTTP |
| `OPCUA_GATEWAY_URL` | OPC-UA Gateway HTTP |
| `INFLUX_URL`, `MINIO_ENDPOINT` | Optionale Metriken/Heatmap-Persistenz |
| `RBAC_ENFORCE` | `true` = Rollen/Permissions erzwingen |
| `LICENSE_ENFORCE`, `LICENSE_ADMIN_TOKEN` | Feature-Gates & Admin-Aktionen |
<<<<<<< HEAD
| `LICENSE_SERVER_URL`, `LICENSE_PRODUCT_ID` | Byte-Commander License Server (Integer-ID) |
=======
| `CAMERA_DRIVER`, `CAMERA_SOURCE`, `CAMERA_SOURCES_JSON` | Edge-Capture / Multi-Kamera-Mapping |
>>>>>>> origin/master

Dev-Auth (nur wenn `ANOMALYMATRIX_ENV` ≠ `prod`): Header `X-AMX-Role` / `X-AMX-User` (Frontend: `VITE_DEV_AUTH_HEADERS=true`) oder `X-AMX-Api-Key`. Unbekannte Rollen werden **abgelehnt** (kein Admin-Fallback).

Produktion: `.env.production.example` · Dev: `.env.example`

## Frontend (HMI)

Seiten: **Dashboard**, **Inspection Detail** (Multi-View + QA-Feedback), **Trends** (Drift je Kamera), **Configuration** (Kameraauswahl 1–4).

```bash
cd frontend
npm install
npm run dev      # Entwicklung
npm run build    # Produktions-Build
npm run smoke    # Build-Check (CI)
```

Optional: `VITE_API_BASE`, `VITE_AMX_ROLE`, `VITE_AMX_FEEDBACK_ROLE` in `.env` im `frontend/`.

## Implementierungsstand vs. BUILD_READY_SPEC

| Bereich | Status |
|---------|--------|
| API-Envelope, Request-ID | ✅ |
| Inspection-Pipeline, Postgres/JSONL | ✅ |
| RBAC (Operator/QA/Engineer/Admin) | ✅ MVP (Header/API-Key) |
| Feedback-Loop + `FeedbackSubmitted` | ✅ |
| Core-Schema (recipes, audit, models, users) | ✅ |
| PatchCore-Inferenz (MVP-Proxy) | ✅ |
| OPC-UA asyncua-Server | ✅ MVP |
| PatchCore Training + Promotion | ✅ v0.8 |
| JWT/Session Auth | ✅ v0.8 |
| OPC-UA Sign/Encrypt | ✅ v0.8 (self-signed) |
| Performance Gate < 500 ms | ✅ v0.8 |
| OpenCV Kamera (Webcam/Datei) | ✅ v0.8 |
| Playwright HMI E2E | ✅ v0.8 |
| Installer v1.2.0 + autonomer Linux-Setup | ✅ |
| WebSocket Live-View, GigE/GenICam | 🔜 Folgerelease |

## Dokumente
- `docs/INSTALLATION.md` — **Installation** (Installer + Compose + lokal)
- `docs/CONFIGURATION.md` — **Konfiguration & Go-Live** (TLS, Kamera, OPC-UA, Rezepte)
- `docs/MULTI_CAMERA.md` — Multi-Kamera Case-Prüfung & Per-Camera-Drift
- `docs/PRODUCTION_RUNBOOK.md` — Betrieb, Backup, Security-Notes
- `docs/PRODUCT_APPLICATION.md` — Anwendung, Einsatzgebiete, Zielgruppen
- `docs/product/EINKAUFSLISTE_LINIE.md` — Hardware-Einkaufsliste Linien-Setup
- `docs/BUILD_READY_SPEC_V1.md` — Ziel-Spezifikation
- `docs/DEPLOYMENT_PLAN.md` — Rollout & Compose-Übersicht
- `docs/RELEASE_READINESS.md` — Freigabe-Checkliste
- `docs/RELEASE_NOTES_v1.2.0.md` — Aktuelles Release
- `docs/MCP_CODEBASE_MEMORY.md` — MCP Code-Intelligence (Cursor / Team)
- `docs/OPS_LICENSE_RUNBOOK.md`, `docs/LICENSE_INTEGRATION.md`

## Tests
```bash
cd backend
py -3 -m pytest -q    # 75+ Tests (Stand v1.2.0)
```

## Release & Installer
- **Aktueller Code-Stand:** `v1.2.0` (Git Tag / `master`)
- **Installer bauen:** `./scripts/build_installer.sh` → `dist/AnomalyMatrix-installer-v1.2.0.run`
- **GitHub Release publizieren:** `./scripts/publish_github_release.sh` (optional `--draft`)
- GitHub: [TheRealByteCommander/AnomalyMatrix](https://github.com/TheRealByteCommander/AnomalyMatrix)

## Hinweise
Dieses Repo folgt dem Byte-Commander-Standard: Abschluss gilt erst nach Merge in Ziel-Branch mit grünem Test-/Review-Gate.
