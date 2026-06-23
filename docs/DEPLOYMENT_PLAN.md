# AnomalyMatrix — Deployment Plan

Stand: **v0.7.0**

## Zielumgebungen

| Umgebung | Zweck | Empfohlener Weg |
|----------|-------|-----------------|
| Entwicklung | Lokale Iteration | Option B (siehe `INSTALLATION.md`) |
| Staging / Pilot | Linientest | Docker Compose |
| Produktion | Dauerbetrieb | Compose oder K8s (Helm folgt) |

## Komponenten

| Service | Port | Pflicht |
|---------|------|---------|
| Backend API | 8080 | ja |
| Frontend HMI | 5173 (dev) / nginx (prod) | ja |
| Edge Acquisition | 8091 | optional (Stub im Backend) |
| OPC-UA Gateway | 8092 HTTP, 4840 OPC-UA | optional |
| Postgres | 5432 | empfohlen |
| InfluxDB / MinIO | 8086 / 9000 | optional |

## Schritte (Docker Compose)

```bash
git clone https://github.com/TheRealByteCommander/AnomalyMatrix.git
cd AnomalyMatrix
cp .env.example .env
docker compose up -d --build
```

1. Postgres-Schema: `scripts/db/003_core_schema.sql` (bei erstem Start via Compose)
2. Backend-Health: `GET http://localhost:8080/api/v1/health`
3. HMI: `cd frontend && npm install && npm run dev` mit `VITE_API_BASE=http://127.0.0.1:8080/api/v1`
4. OPC-UA (optional): Gateway starten, PLC-Bridge konfigurieren (`opcua-gateway/README.md`)

## Konfiguration (wichtig)

```env
ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore
DATABASE_URL=postgresql://...
RBAC_ENFORCE=true
```

## Rollout-Checkliste

1. [ ] Secrets (.env) nicht in Git
2. [ ] `RBAC_ENFORCE=true` in Staging/Prod
3. [ ] Backup Postgres + `backend/data/` (JSONL-Fallback)
4. [ ] Smoke: `POST /api/v1/inspections/run` + HMI Dashboard
5. [ ] OPC-UA: Trigger-Test mit SPS-Simulator

## Rollback

- Compose: vorheriges Image-Tag / `git checkout` + `docker compose up -d --build`
- Daten: Postgres-Snapshot wiederherstellen

## Monitoring

- `GET /api/v1/observability/summary`
- Domain-Events: `GET /api/v1/events/recent`
- Logs: Container-Stdout (strukturierte JSON-Logs geplant)
