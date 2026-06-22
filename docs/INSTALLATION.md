# AnomalyMatrix Installation

Stand: **v0.6.0** (API + HMI + Gateway)

## Option A: One-file installer (.run)

Build installer from repository root:

```bash
./scripts/build_installer.sh
```

Run installer:

```bash
./dist/AnomalyMatrix-installer.run
```

Optional env overrides:

```bash
APP_DIR=/opt/anomalymatrix BRANCH=master ./dist/AnomalyMatrix-installer.run
```

> Der Installer basiert auf Release **v0.1.0**. Für den neuesten Code-Stand: Option B/C oder `git pull` + Docker Compose.

## Option B: Direct install script

```bash
./scripts/install.sh
```

## Option C: Lokale Entwicklung (Windows)

### Voraussetzungen
- **Python 3.12+** (`py -3`)
- **Node.js 18+** (z. B. `winget install OpenJS.NodeJS.18` — Paket-ID `OpenJS.NodeJS.18`, nicht `OpenJS.NodeJS.LTS`)
- Optional: **Docker Desktop** für vollständigen Stack

### Backend
```powershell
cd backend
py -3 -m pip install -r requirements.txt
copy ..\.env.example ..\.env
py -3 -m uvicorn app.main:app --reload --port 8080
```

Health-Check: `curl http://127.0.0.1:8080/api/v1/health`

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

UI: [http://localhost:5173](http://localhost:5173)

**Häufiger Fehler:** `ERR_CONNECTION_REFUSED` auf Port 5173 → `npm run dev` läuft nicht oder Terminal wurde geschlossen.

Falls `localhost` nicht antwortet: [http://127.0.0.1:5173](http://127.0.0.1:5173) oder `npm run dev -- --host 127.0.0.1`

### Edge + OPC-UA (optional, ohne Docker)
```powershell
# Terminal: edge-acquisition (8091)
cd edge-acquisition
py -3 -m pip install -r requirements.txt
py -3 -m uvicorn service:app --port 8091

# Terminal: opcua-gateway (8092 HTTP, 4840 OPC-UA)
cd opcua-gateway
py -3 -m pip install -r requirements.txt
py -3 -m uvicorn gateway_service:app --port 8092
```

In `.env`: `EDGE_ACQUISITION_URL=http://127.0.0.1:8091`, `OPCUA_GATEWAY_URL=http://127.0.0.1:8092`

## Option D: Docker Compose (empfohlen für Integration)

```bash
cp .env.example .env
docker compose up --build
```

Startet API, Postgres (mit `scripts/db/*.sql`), InfluxDB, MinIO, edge-acquisition, opcua-gateway.

| Service | URL |
|---------|-----|
| API | http://localhost:8080 |
| Frontend (lokal) | http://localhost:5173 (`npm run dev` separat) |
| OPC-UA | `opc.tcp://localhost:4840/anomalymatrix/server/` |
| MinIO Console | http://localhost:9001 |

## Datenbank-Migrationen

Bei Docker: automatisch via `scripts/db/` → `/docker-entrypoint-initdb.d`.

Manuell (Postgres läuft):
```bash
./scripts/db/apply_migrations.sh
```

Skripte:
- `001_init.sql` — Inspection-Ergebnisse
- `002_payload_jsonb.sql` — JSONB-Payload
- `003_core_schema.sql` — recipes, users, roles, audit_log, feedback_events, model_registry

Ohne `DATABASE_URL` nutzt die API JSONL unter `backend/data/`.

## RBAC & Feedback (Dev)

`.env`: `RBAC_ENFORCE=false` (Standard) — Header `X-AMX-Role` / `X-AMX-User` für Tests.

Mit Postgres-Seed (`003_core_schema.sql`):
- `amx-key-operator`, `amx-key-qa`, `amx-key-engineer`, `amx-key-admin`

Feedback erfordert Rolle `qa_lead` oder `admin` (wenn `RBAC_ENFORCE=true`).

## Inferenz-Provider

```env
ANOMALYMATRIX_INFERENCE_PROVIDER=stub          # Default
ANOMALYMATRIX_INFERENCE_PROVIDER=opencv_ready
ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore     # OpenCV-Textur + Hash-Proxy
```

## What installer does
1. Validates required tooling (`git`, `docker`, `docker compose`, `curl`)
2. Clones/updates repo to target directory
3. Creates `.env` from `.env.example` if missing
4. Starts stack via Docker Compose
5. Runs DB migration script (if available)
6. Performs API health check

## Data safety
- Persistent data uses Docker named volumes (`postgres_data`, `influx_data`, `minio_data`).
- Re-running installer updates code but does not wipe volumes.
- To remove stack without deleting volumes:

```bash
docker compose -f /opt/anomalymatrix/docker-compose.yml --env-file /opt/anomalymatrix/.env down
```

- To fully wipe data (destructive):

```bash
docker compose -f /opt/anomalymatrix/docker-compose.yml --env-file /opt/anomalymatrix/.env down -v
```

## Verifikation nach Installation

```bash
cd backend && py -3 -m pytest -q
curl http://127.0.0.1:8080/api/v1/health
curl http://127.0.0.1:8092/health
```
