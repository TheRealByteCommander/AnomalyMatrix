# AnomalyMatrix

Engineering-first MVP scaffold for industrial anomaly detection stack.

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
