# infra

Infrastructure-Manifeste für AnomalyMatrix **v1.2.0**.

## Compose (Repo-Root)
- `docker-compose.yml` — Core-Stack
- `docker-compose.dev.yml` — Dev-Ports
- `docker-compose.prod.yml` — Produktion
- `docker-compose.camera.yml` — OpenCV-Gerätedurchreichung
- `docker-compose.tls.yml` — Caddy TLS-Termination

## Caddy TLS
Beispiel-Config: `infra/caddy/Caddyfile` (Certs unter `./certs/tls.crt` + `tls.key`).

## Volumes
- `postgres_data`, `influx_data`, `minio_data`, `api_data`, `opcua_certs`

Kubernetes/Helm: noch nicht implementiert (optional für Folgerelease).

Siehe `docs/INSTALLATION.md`, `docs/PRODUCTION_RUNBOOK.md`.
