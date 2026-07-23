# AnomalyMatrix — Deployment Plan

Stand: **v1.1.0**

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
2. [ ] `RBAC_ENFORCE=true` / `SERVICE_AUTH_TOKEN` gesetzt
3. [ ] `/api/v1/health` und `/api/v1/ready` grün
4. [ ] Volume `api_data` + `opcua_certs` vorhanden
5. [ ] TLS (`docker-compose.tls.yml` oder Reverse-Proxy) + `COOKIE_SECURE=true`
6. [ ] Kamera konfiguriert (`synthetic` bewusst oder `docker-compose.camera.yml`)
7. [ ] OPC-UA: Kunden-PKI + SPS-Trigger-Test
8. [ ] Backup Postgres (`MODE=prod ./scripts/backup/backup.sh`)
9. [ ] Smoke: Login + Inspektion + HMI Dashboard

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [`INSTALLATION.md`](./INSTALLATION.md) | Install (Installer / Compose / lokal) |
| [`CONFIGURATION.md`](./CONFIGURATION.md) | **Konfiguration & Go-Live** |
| [`PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md) | Betrieb, Backup, Security |
| [`RELEASE_READINESS.md`](./RELEASE_READINESS.md) | Freigabe-Status |

## Rollback

- Compose: vorheriges Image-Tag / `git checkout` + `compose up -d --build`
- Daten: `MODE=prod ./scripts/backup/restore.sh backups/<timestamp>`

## Monitoring

- `GET /api/v1/observability/summary`
- Domain-Events: `GET /api/v1/events/recent`
- Logs: `docker compose ... logs -f api`
- Readiness: `GET /api/v1/ready`

