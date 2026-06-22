# infra

Infrastructure-Manifeste für AnomalyMatrix.

## Stand v0.6.0
- **Produktions-Runtime:** Docker Compose im Repo-Root (`docker-compose.yml`)
- Services: api, postgres, influxdb, minio, edge-acquisition, opcua-gateway
- Kubernetes/Helm: noch nicht implementiert (optional für Folgerelease)

## Volumes (Compose)
- `postgres_data`, `influx_data`, `minio_data`

Siehe `docs/INSTALLATION.md` und `README.md`.
