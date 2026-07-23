# AnomalyMatrix v1.1.0 – Release Notes

**Datum:** 2026-07-23  
**Tag:** `v1.1.0`  
**Basis:** `master` nach Full-Release-Gaps, Docs und CI-Stabilisierung

## Status

**Pilot- / kontrollierter OT-Deploy ready** (wie v1.0.0), mit geschlossenem Betriebspfad:

- Readiness-Endpoint und Image-Builds in CI
- TLS-/Kamera-Compose-Overlays
- Aktuelle Installations- und Konfigurationsdoku
- Stack fest auf **Python 3.12** / **Node 20** (grünes CI)

## Highlights seit v1.0.0

### Betrieb & Freigabe (#33)
- `GET /api/v1/ready` neben `/health` (DB + Abhängigkeiten)
- CI baut API-, Edge- und OPC-UA-Images
- Compose: Healthchecks, Artifacts, TLS-Overlay (`docker-compose.tls.yml`), Kamera-Overlay (`docker-compose.camera.yml`)
- Installer hard-fail bei kritischen Post-Install-Schritten
- OpenAPI in Prod restriktiver; Backup/Restore und Runbook nachgezogen
- Dependabot Docker-Ignores für Python ≥ 3.13 und Node-Major

### Dokumentation (#40)
- Neu: `docs/CONFIGURATION.md` (Secrets, Auth, OPC-UA, Kamera, TLS, Env)
- `docs/INSTALLATION.md` an aktuellen Installer und Ready-Checks angepasst

### Plattform / CI (#44 + Deps)
- Dockerfiles und CI auf **python:3.12-slim** und **node:20**
- Dependency-Updates: NumPy 2.5, OpenCV 5, psycopg2 2.9.12, Influx-Client, Nginx

## Install

### Frisches Ubuntu Server 24.04 LTS

```bash
# Variante A — One-liner (Release-Tag)
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/v1.1.0/scripts/install.sh \
  | sudo bash -s -- --host <SERVER-IP> --branch v1.1.0

# Variante B — Release-Asset
sudo ./AnomalyMatrix-installer-v1.1.0.run --host <SERVER-IP>

# Mit TLS-Terminierung / Secure Cookies
sudo ./AnomalyMatrix-installer-v1.1.0.run --host <SERVER-IP> --tls
```

### Aus bestehendem Checkout

```bash
git fetch origin tag v1.1.0
git checkout v1.1.0
sudo ./scripts/install.sh --mode prod --host <SERVER-IP>
```

Nach dem Install: [`docs/CONFIGURATION.md`](./CONFIGURATION.md) · [`docs/PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md)

## Upgrade von v1.0.0

1. Backup: `scripts/backup/backup.sh` (siehe Runbook)
2. Auf `v1.1.0` auschecken bzw. Installer mit `--branch v1.1.0` (ohne `--force-secrets`, sofern Secrets behalten werden sollen)
3. Stack neu bauen/starten; `/api/v1/health` und `/api/v1/ready` prüfen
4. Optional TLS-/Kamera-Overlays aktivieren

## Explizit unverändert / weiterhin Kundenpflicht

- TLS-Terminierung vor dem HMI (Caddy/Compose-TLS-Overlay vorbereiten, Zertifikate stellen)
- OPC-UA Kunden-PKI (Sign/Encrypt)
- Kamera-/SPS-Anbindung und Rezepte vor Go-Live
- Kein bedingungsloses 24/7 ohne Rollout-Gates in `docs/RELEASE_READINESS.md`

## Assets

| Datei | Beschreibung |
|-------|--------------|
| `AnomalyMatrix-installer-v1.1.0.run` | Self-extracting Installer |
| `AnomalyMatrix-installer.run` | Alias auf aktuelle Version |
| `SHA256SUMS.txt` | Prüfsummen der Assets |

Siehe auch: `docs/RELEASE_NOTES_v1.0.0.md` für den v1.0.0-Baseline.
