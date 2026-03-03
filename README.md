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
