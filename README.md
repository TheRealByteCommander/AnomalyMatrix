# AnomalyMatrix

Engineering-first MVP scaffold for industrial anomaly detection stack.

**Aktueller Stand:** Phase 3 (Real Path) + License Integration v1 abgeschlossen und gemerged.
**Deployment Baseline:** `v0.1.0`

## Ziele
- Unüberwachte Anomalieerkennung auf Gut-Teilen
- Continual-Learning Feedback-Loop (Human-in-the-Loop)
- OPC-UA Integration (Machine Vision Companion Spec)
- Tesla-inspiriertes, operator-first HMI
- Trendanalyse & Frühwarnungen für Prozessdrift

## Repository Layout
- `backend/` FastAPI service bootstrap
- `frontend/` UI workspace
- `edge-acquisition/` edge capture service
- `opcua-gateway/` OPC UA integration service
- `infra/` infra manifests
- `scripts/` automation scripts
- `tests/` top-level integration test workspace
- `contracts/` versioned shared contracts

## Backend quick start
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --port 8080
```

API examples:
- `GET /api/v1/health`
- `GET /api/v1/contracts/events`
- `GET /api/v1/license/status`
- `POST /api/v1/license/activate`
- `POST /api/v1/license/deactivate`

## Docker Compose baseline
```bash
docker compose up --build
```

Starts:
- API (8080)
- Postgres (5432)
- InfluxDB (8086)
- MinIO (9000/9001)

## Dokumente
- `docs/BUILD_READY_SPEC_V1.md`
- `docs/IMPLEMENTATION_NOTES_MVP_SCAFFOLD.md`
- `docs/IMPLEMENTATION_PLAN_V0.1.md`
- `docs/KONZEPT_ORIGINAL_2026-02-24.md`
- `docs/INSTALLATION.md` (vollständige Installation inkl. Installer-Datei)
- `docs/PHASE3_REAL_PATH.md`
- `docs/RELEASE_NOTES_v0.1.0.md`
- `docs/product/PHASE3_VALUE_AND_KPI_PLAN.md`

## Hinweise
Dieses Repo folgt dem Byte-Commander-Standard: Abschluss gilt erst nach Merge in Ziel-Branch mit grünem Test-/Review-Gate.

## Frontend MVP Scaffold (UX/UI)

Path: `frontend/`

Pages (clickable wireframe):
- Dashboard
- Inspection Detail
- Trends
- Configuration

Run locally:
```bash
cd frontend
npm install
npm run dev
```

Build check:
```bash
npm run build
```

## Phase 2 Vertical MVP Flow

Backend endpoints:
- `POST /api/v1/inspections/run`
- `GET /api/v1/inspections/recent`

Frontend behavior:
- Dashboard can trigger inspection pipeline.
- Latest result becomes clickable into Inspection Detail.
- Trends page reflects latest synthetic inspections.

Validation:
```bash
cd backend
pytest -q

cd ../frontend
npm install
npm run smoke
```


## Phase 2 Vertical Flow

New endpoints:
- `POST /api/v1/edge/capture`
- `POST /api/v1/ai/infer`
- `POST /api/v1/orchestrate/run-inspection`
- `GET /api/v1/results/latest`

Compatibility aliases kept:
- `POST /api/v1/inspections/run`
- `GET /api/v1/inspections/recent`


## Phase 3 Real Path

- Pluggable inference provider: `ANOMALYMATRIX_INFERENCE_PROVIDER=stub|opencv_ready`
- Query APIs:
  - `GET /api/v1/results/query`
  - `GET /api/v1/results/trend-summary`
- OPC-UA payload mapping + publish integration in run-inspection flow.
- DB migration scripts under `scripts/db/`.

## License Integration v1

- Lizenzsystem-Integration auf Basis des separaten Repos `software-licensing-concept`.
- Backend-Endpunkte:
  - `GET /api/v1/license/status`
  - `POST /api/v1/license/activate`
  - `POST /api/v1/license/deactivate`
- Feature-Gating ist integriert (`inspection.run`, `inspection.read`, etc.).
- Offline/Grace- und Statuszustände werden im Lizenzstatus geführt.

Konfiguration (ENV, Auszug):
- `LICENSE_ADMIN_TOKEN` (für administrative Lizenzaktionen)
- `LICENSE_STATE_FILE` (Persistenzpfad Lizenzstatus)
- `LICENSE_ENFORCE` (Feature-Gates strikt erzwingen)

## Release & Installer

- Baseline Release: `v0.1.0`
- GitHub Release: `https://github.com/TheRealByteCommander/AnomalyMatrix/releases/tag/v0.1.0`
- Installer-Dateien:
  - `dist/AnomalyMatrix-installer.run`
  - `dist/AnomalyMatrix-installer-v0.1.0.run`
