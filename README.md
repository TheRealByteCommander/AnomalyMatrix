# AnomalyMatrix

Engineering-first MVP for industrial anomaly detection (unüberwachte Gut-Teil-Prüfung, Operator-HMI, OPC-UA-Anbindung).

**Aktueller Stand (2026-06):** API **v0.6.0** auf `master`  
**Deployment Baseline:** `v0.6.0` (lokal/Docker); Installer-Artefakt weiterhin `v0.1.0`

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
| **Trends** | Prozessdrift früh erkennen, bevor Serienfehler entstehen |

Ausführliche Beschreibung (DE/EN): **Hilfe & FAQ** im HMI oder `docs/PRODUCT_APPLICATION.md`.

## Repository Layout
| Pfad | Inhalt |
|------|--------|
| `backend/` | FastAPI API (Inspection, RBAC, License, Observability) |
| `frontend/` | React/Vite HMI (Dashboard, Detail, Trends, Config) |
| `edge-acquisition/` | HTTP Capture-Service (synthetisch / Stub) |
| `opcua-gateway/` | HTTP `/publish` + asyncua OPC-UA-Server (Port 4840) |
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

## Docker Compose
```bash
docker compose up --build
```

| Service | Port |
|---------|------|
| API | 8080 |
| edge-acquisition | 8091 |
| opcua-gateway (HTTP) | 8092 |
| opcua-gateway (OPC-UA) | 4840 |
| Postgres | 5432 |
| InfluxDB | 8086 |
| MinIO | 9000 / 9001 |

DB-Init-Skripte werden aus `scripts/db/` in Postgres geladen (`001`–`003`).

## API v0.6.0 (Auszug)

### Inspection & Ergebnisse
- `POST /api/v1/inspections/run` (Alias: `/orchestrate/run-inspection`)
- `GET /api/v1/inspections/recent` (Alias: `/results/latest`)
- `GET /api/v1/results/query`
- `GET /api/v1/results/trend-summary`
- `POST /api/v1/edge/capture`, `POST /api/v1/ai/infer`

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
| `DATABASE_URL` | Postgres (Compose); leer = JSONL-Fallback |
| `ANOMALYMATRIX_INFERENCE_PROVIDER` | `stub` \| `opencv_ready` \| `patchcore` |
| `EDGE_ACQUISITION_URL` | Edge-Capture HTTP |
| `OPCUA_GATEWAY_URL` | OPC-UA Gateway HTTP |
| `INFLUX_URL`, `MINIO_ENDPOINT` | Optionale Metriken/Heatmap-Persistenz |
| `RBAC_ENFORCE` | `true` = Rollen/Permissions erzwingen |
| `LICENSE_ENFORCE`, `LICENSE_ADMIN_TOKEN` | Feature-Gates & Admin-Aktionen |

Dev-Auth (wenn `RBAC_ENFORCE=false`): Header `X-AMX-Role`, `X-AMX-User` oder `X-AMX-Api-Key` (Seed-Keys in `scripts/db/003_core_schema.sql`).

Vollständige Liste: `.env.example`

## Frontend (HMI)

Seiten: **Dashboard**, **Inspection Detail** (inkl. QA-Feedback), **Trends**, **Configuration** (Recipes/Models aus API).

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
| Influx/MinIO/Observability | ✅ optional |
| Echtes Modell-Training, JWT-Auth, E2E-Gates | 🔜 Folgerelease |

## Dokumente
- `docs/INSTALLATION.md` — Installation (Installer + lokal)
- `docs/PRODUCT_APPLICATION.md` — Anwendung, Einsatzgebiete, Zielgruppen
- `docs/BUILD_READY_SPEC_V1.md` — Ziel-Spezifikation
- `docs/IMPLEMENTATION_NOTES_MVP_SCAFFOLD.md` — Umsetzungsnotizen
- `docs/PHASE3_REAL_PATH.md` — Real-Path / Provider / Persistenz
- `docs/RELEASE_NOTES_v0.6.0.md` — Aktuelles Release
- `docs/RELEASE_NOTES_v0.1.0.md` — Baseline-Installer-Release
- `docs/OPS_LICENSE_RUNBOOK.md`, `docs/LICENSE_INTEGRATION.md`

## Tests
```bash
cd backend
py -3 -m pytest -q    # 27+ Tests (Stand v0.6.0)
```

## Release & Installer
- **Aktueller Code-Stand:** `v0.6.0` (Git `master`)
- **Installer-Baseline:** `v0.1.0` — `dist/AnomalyMatrix-installer-v0.1.0.run`
- GitHub: [TheRealByteCommander/AnomalyMatrix](https://github.com/TheRealByteCommander/AnomalyMatrix)

## Hinweise
Dieses Repo folgt dem Byte-Commander-Standard: Abschluss gilt erst nach Merge in Ziel-Branch mit grünem Test-/Review-Gate.
