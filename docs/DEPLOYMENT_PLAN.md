# AnomalyMatrix — Deployment Plan

Stand: **v1.0.0**

## Zielumgebungen

| Umgebung | Zweck | Empfohlener Weg |
|----------|-------|-----------------|
| Entwicklung | Lokale Iteration | Compose Dev-Overlay |
| Staging / Pilot | Linientest | Compose Prod-Overlay |
| Produktion | Dauerbetrieb | `scripts/install.sh` oder Compose Prod |

## Komponenten

| Service | Dev-Port | Prod | Pflicht |
|---------|----------|------|---------|
| Backend API | 8080 | localhost:8080 | ja |
| Frontend HMI | — | 80 (nginx) | ja |
| Edge Acquisition | 8091 | intern | empfohlen |
| OPC-UA Gateway | 8092 / 4840 | 4840 | empfohlen |
| Postgres | 5432 | intern | ja (Prod) |
| InfluxDB / MinIO | 8086 / 9000 | intern | optional |

## Schritte

### Autonom (frisches Ubuntu 24.04 LTS)

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
  | sudo bash -s -- --host <SERVER-IP>
```

### Produktion (manuell)

```bash
cp .env.production.example .env.production   # Secrets ersetzen
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production up -d --build
```

### Entwicklung

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml \
  --env-file .env up --build
```

1. Postgres-Schema: `scripts/db/*.sql` (bei erstem Start via Compose)
2. Backend-Health: `GET http://127.0.0.1:8080/api/v1/health`
3. HMI: Port 80 (Prod) bzw. `cd frontend && npm run dev` (Dev)
4. OPC-UA: PLC-Bridge konfigurieren (`opcua-gateway/README.md`)

## Konfiguration (wichtig)

```env
ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore
DATABASE_URL=postgresql://...
RBAC_ENFORCE=true
SERVICE_AUTH_TOKEN=...
```

## Rollout-Checkliste

1. [ ] Secrets (`.env.production`) nicht in Git
2. [ ] `RBAC_ENFORCE=true` in Staging/Prod
3. [ ] Volume `api_data` für License-State vorhanden
4. [ ] Backup Postgres + Volumes
5. [ ] Smoke: Login + `POST /api/v1/inspections/run` + HMI Dashboard
6. [ ] OPC-UA: Trigger-Test mit SPS-Simulator

## Rollback

- Compose: vorheriges Image-Tag / `git checkout` + `compose up -d --build`
- Daten: Postgres-Snapshot / Volume-Restore

## Monitoring

- `GET /api/v1/observability/summary`
- Domain-Events: `GET /api/v1/events/recent`
- Logs: `docker compose ... logs -f api`
