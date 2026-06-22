# AnomalyMatrix v0.6.0 – Release Notes

**Datum:** 2026-06  
**Branch:** `master`  
**API-Version:** 0.6.0

## Highlights

### Core Data Layer
- Postgres-Schema `003_core_schema.sql`: `roles`, `users`, `recipes`, `model_registry`, `audit_log`, `feedback_events`
- `CoreStore`: Postgres mit JSONL-Fallback wenn `DATABASE_URL` leer

### RBAC (IEC 62443-orientiert, MVP)
- Rollen: Operator, QA Lead, Process Engineer, Admin
- Permissions auf Inspection-, Catalog-, Feedback- und License-Endpunkten
- Auth: `X-AMX-Api-Key` (DB-Seed) oder Dev-Header `X-AMX-Role` / `X-AMX-User`
- `RBAC_ENFORCE=true` für strikte Erzwingung

### Feedback-Loop
- `POST /api/v1/feedback`, `GET /api/v1/feedback`
- Verdicts: `confirm_anomaly`, `false_positive`, `needs_review`
- Domain-Event `FeedbackSubmitted`, Audit-Log-Eintrag
- HMI: Feedback-Formular auf Inspection Detail

### Catalog API
- `GET /api/v1/recipes`, `GET /api/v1/models`, `GET /api/v1/audit/recent`
- Configuration-Seite lädt Recipes/Models aus API

### PatchCore Inference (MVP)
- Provider `patchcore`: OpenCV Laplacian-Textur + Metadata-Hash-Proxy
- Dependencies: `numpy`, `opencv-python-headless`

### OPC-UA Gateway
- asyncua Background-Server (Port **4840**)
- HTTP `/publish` schreibt Nodes + OPC-UA-Variablen
- Docker Compose exponiert 4840

### Observability (aus v0.5, weiterhin aktiv)
- Influx-Metriken, MinIO-Heatmaps (optional)
- `GET /api/v1/observability/summary`, `GET /api/v1/events/recent`

## Frontend
- API-Header für RBAC-Rollen
- QA-Feedback auf Inspection Detail
- Configuration zeigt Live-Recipe/Model aus Backend

**Voraussetzung:** Node.js 18+ (`npm run dev` → Port 5173)

## Tests
```bash
cd backend && py -3 -m pytest -q
```
27 Tests grün (Stand Release).

## Upgrade von v0.5 / v0.1.0
1. `git pull origin master`
2. `py -3 -m pip install -r backend/requirements.txt`
3. Postgres: Migration `003_core_schema.sql` (Docker: automatisch bei neuem Volume; sonst `apply_migrations.sh`)
4. Optional `.env`: `RBAC_ENFORCE`, `ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore`
5. Frontend: `cd frontend && npm install && npm run dev`

## Bekannte Grenzen
- Kein echtes Modell-Training; PatchCore ist MVP-Proxy
- RBAC ohne Passwort/JWT — nur API-Key/Header
- Installer-Artefakt weiterhin v0.1.0-Baseline (manueller Pull empfohlen)
