# AnomalyMatrix Installation

Stand: **v1.0.0** (Production-hardened)

## Welches Linux?

| Distro | Empfehlung | Kommentar |
|--------|------------|-----------|
| **Ubuntu Server 24.04 LTS** | **Primär empfohlen** | Beste Docker-Unterstützung, 5 Jahre Updates, üblich an OT/Edge-Geräten |
| Ubuntu Server 22.04 LTS | Unterstützt | Ebenfalls LTS, etwas ältere Pakete |
| Debian 12 (bookworm) | Unterstützt | Minimaler Footprint, etwas mehr manuelle Pflege |

**Nicht empfohlen:** Desktop-Varianten (unötig), Rolling Releases, Alpine als Host (Docker-Engine-Repo).

Hardware-Minimum (Pilot): 4 vCPU, 8 GB RAM, 40 GB SSD, x86_64 oder aarch64.

---

## Autonome Installation (frisches OS)

Ab einem neu installierten Ubuntu Server (nur SSH-Zugang):

```bash
# Öffentliches Repo / Release-Branch
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
  | sudo bash

# Mit Host-IP/DNS und ohne Firewall-Änderung
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
  | sudo bash -s -- --host 192.168.10.50 --no-firewall

# Privates Repo
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
  | sudo GITHUB_TOKEN=ghp_xxx bash -s -- --host anomalymatrix.factory.local
```

Aus einem bereits ausgecheckten Repo:

```bash
sudo ./scripts/install.sh --mode prod --host 192.168.10.50
```

### Was das Skript macht

1. OS prüfen (Ubuntu 22.04/24.04, Debian 12)
2. Basispakete + **Docker Engine + Compose Plugin** installieren
3. Repo nach `/opt/anomalymatrix` klonen bzw. synchronisieren
4. Starke Secrets generieren → `.env.production` + `CREDENTIALS.txt` (Mode 600)
5. Production-Stack bauen & starten (`docker-compose.yml` + `docker-compose.prod.yml`)
6. Health-Check, Admin-Bootstrap, Lizenz-Aktivierung, Smoke-Inspektion
7. UFW (22/80/4840) + `systemd`-Unit `anomalymatrix` für Autostart

Nach dem Lauf:

| Was | Wo |
|-----|-----|
| HMI | `http://<HOST>/` |
| Admin | `admin-1` / Passwort in `/opt/anomalymatrix/CREDENTIALS.txt` |
| API | `http://127.0.0.1:8080/api/v1/health` |
| Install-Log | `/var/log/anomalymatrix-install.log` |

### Installer-Optionen

```
--mode prod|dev     Standard: prod
--host HOST         IP/DNS für CORS und Anzeige-URLs
--app-dir DIR       Standard: /opt/anomalymatrix
--branch BRANCH     Standard: master
--repo-url URL      Git-Remote
--skip-clone        Vorhandenen Code nutzen
--skip-docker       Docker nicht neu installieren
--force-secrets     .env.production neu generieren (gefährlich — bricht DB-Volumes)
--no-firewall       UFW nicht anfassen
--tls               HTTPS erwartet (COOKIE_SECURE=true)
```

> Re-Install **ohne** `--force-secrets` behält `.env.production` und bestehende Postgres-Volumes.
---

## Option A: One-file installer (.run)

```bash
./scripts/build_installer.sh
sudo ./dist/AnomalyMatrix-installer.run --host 192.168.10.50
```

Der `.run`-Wrapper entpackt `scripts/install.sh` und führt es aus.

---

## Option B: Docker Compose manuell

### Produktion

```bash
cp .env.production.example .env.production   # Secrets ersetzen
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production up -d --build
```

### Entwicklung (Ports auf dem Host)

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml \
  --env-file .env up --build
```

| Service | Dev-Port | Prod |
|---------|----------|------|
| HMI (nginx) | — | **80** |
| API | 8080 | localhost:8080 |
| edge-acquisition | 8091 | nur Docker-Netz |
| opcua-gateway HTTP | 8092 | nur Docker-Netz |
| OPC-UA | 4840 | **4840** |
| Postgres / Influx / MinIO | 5432 / 8086 / 9000 | nur Docker-Netz |

---

## Option C: Lokale Entwicklung (ohne Docker)

### Voraussetzungen
- **Python 3.11+**
- **Node.js 18+**

### Backend
```bash
cd backend
python3 -m pip install -r requirements.txt
cp ../.env.example ../.env
python3 -m uvicorn app.main:app --reload --port 8080
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Datenbank-Migrationen

Bei Docker: automatisch via `scripts/db/` → `/docker-entrypoint-initdb.d` (`001`–`005`).

Manuell: `./scripts/db/apply_migrations.sh`

---

## Data safety

- Persistenz über Docker-Volumes (`postgres_data`, `influx_data`, `minio_data`, `opcua_certs`)
- Installer überschreibt Volumes **nicht**
- Credentials: `/opt/anomalymatrix/CREDENTIALS.txt` nach Übernahme in den Vault löschen

```bash
# Stack stoppen (Daten behalten)
sudo systemctl stop anomalymatrix

# Stack inkl. Volumes löschen (destruktiv)
cd /opt/anomalymatrix
docker compose -p anomalymatrix -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production down -v
```

## Verifikation

```bash
curl -fsS http://127.0.0.1:8080/api/v1/health
sudo cat /opt/anomalymatrix/CREDENTIALS.txt
curl -fsS -c /tmp/amx.cookie -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"admin-1","password":"<AUS_CREDENTIALS>"}'
```

Siehe auch: `docs/PRODUCTION_RUNBOOK.md`, `docs/RELEASE_READINESS.md`.
