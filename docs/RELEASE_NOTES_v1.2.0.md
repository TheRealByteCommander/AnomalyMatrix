# AnomalyMatrix v1.2.0 – Release Notes

**Datum:** 2026-07-28  
**Tag:** `v1.2.0`  
**Basis:** `master` nach Multi-Kamera (#48) und License-Server (#47)

## Status

**Pilot- / kontrollierter OT-Deploy ready** (wie v1.1.0), erweitert um:

- Multi-Kamera Case-Prüfung (1–4 Views, worst-view)
- Drift-Auswertung **pro Kamera** (API, HMI, OPC-UA)
- Byte-Commander License Server (optionaler Remote-Mode)
- Contract `inspection_result` / OPC-UA-Mapping **v1.2**

## Highlights seit v1.1.0

### Multi-Kamera Case-Prüfung (#48)
- Hardware-Discovery am Edge (`GET /cameras`) und Stationsauswahl 1–4
- API: `GET/PUT /api/v1/cameras`, `/cameras/selection`
- `/inspections/run` mit Multi-View (`views`, `camera_ids`, `worst_view_camera_id`, `decision_policy=worst_view`)
- Persistenz der Auswahl (`station_cameras.json`)
- OPC-UA: leeres `Request.CameraId` → Stationsauswahl; LastResult mit CameraIds / ViewCount / WorstViewCameraId
- HMI: Konfiguration (Kamera-Picker), Detail (Multi-View), Trends (Drift je Kamera)
- Doku: [`MULTI_CAMERA.md`](./MULTI_CAMERA.md)

### Per-Camera Drift (#48)
- Trend-Summary / Observability: `by_camera[]`, `drifting_camera_id`, `drift_score`, `score_delta`, `baseline_avg_score`
- Trend-Warnung nennt die driftende Kamera (`camera_drift:<id>:…`)
- OPC-UA Trend-Nodes: Severity, Reason, DriftingCameraId, DriftScore, ScoreDelta

### License Server (#47)
- Optionaler Remote-Mode: `LICENSE_SERVER_URL` + Integer-`LICENSE_PRODUCT_ID`
- Lokale `AMX-*`-Keys weiterhin ohne Server nutzbar
- SDK unter `backend/app/licensing_sdk/`
- Doku: [`LICENSE_INTEGRATION.md`](./LICENSE_INTEGRATION.md), [`OPS_LICENSE_RUNBOOK.md`](./OPS_LICENSE_RUNBOOK.md)

### Contracts
- `contracts/inspection_result_v1.json` → **1.2.0**
- `contracts/opcua_nodeset_mapping_v1.json` → **1.2.0**

## Install

### Frisches Ubuntu Server 24.04 LTS

```bash
# Variante A — One-liner (Release-Tag)
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/v1.2.0/scripts/install.sh \
  | sudo bash -s -- --host <SERVER-IP> --branch v1.2.0

# Variante B — Release-Asset
sudo ./AnomalyMatrix-installer-v1.2.0.run --host <SERVER-IP>

# Mit TLS-Terminierung / Secure Cookies
sudo ./AnomalyMatrix-installer-v1.2.0.run --host <SERVER-IP> --tls
```

### Aus bestehendem Checkout

```bash
git fetch origin tag v1.2.0
git checkout v1.2.0
sudo ./scripts/install.sh --mode prod --host <SERVER-IP>
```

Nach dem Install: [`CONFIGURATION.md`](./CONFIGURATION.md) · [`PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md) · [`MULTI_CAMERA.md`](./MULTI_CAMERA.md)

## Upgrade von v1.1.0

1. Backup: `scripts/backup/backup.sh` (siehe Runbook)
2. Auf `v1.2.0` auschecken bzw. Installer mit `--branch v1.2.0` (ohne `--force-secrets`, sofern Secrets behalten werden sollen)
3. Stack neu bauen/starten; `/api/v1/health` und `/api/v1/ready` prüfen
4. Multi-Kamera: Auswahl 1–4 in HMI Konfiguration speichern; SPS-Trigger mit leerem CameraId abstimmen
5. Optional License Server: `LICENSE_SERVER_URL` + `LICENSE_PRODUCT_ID` setzen

## Explizit unverändert / weiterhin Kundenpflicht

- Capture bleibt **sequentiell** (kein Hardware-Trigger-Sync zwischen Kameras)
- TLS-Terminierung vor dem HMI
- OPC-UA Kunden-PKI (Sign/Encrypt)
- Kamera-/SPS-Anbindung und Rezepte vor Go-Live
- Kein bedingungsloses 24/7 ohne Rollout-Gates in `docs/RELEASE_READINESS.md`

## Assets

| Datei | Beschreibung |
|-------|--------------|
| `AnomalyMatrix-installer-v1.2.0.run` | Self-extracting Installer |
| `AnomalyMatrix-installer.run` | Alias auf aktuelle Version |
| `SHA256SUMS.txt` | Prüfsummen der Assets |

Siehe auch: `docs/RELEASE_NOTES_v1.1.0.md` für den vorherigen Stand.
