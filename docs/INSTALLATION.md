# AnomalyMatrix Installation

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

## Option B: Direct install script

```bash
./scripts/install.sh
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
