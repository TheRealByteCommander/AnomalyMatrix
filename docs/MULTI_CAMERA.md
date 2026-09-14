# Multi-Kamera Case-Prüfung & Drift

Stand: **v1.2.0**

Mehrere Kameras (Hardware-erkannt) prüfen **denselben Case**. Ergebnis-Aggregation: **worst view wins**. Drift wird **pro Kamera** ausgewiesen.

Verwandt: [`CONFIGURATION.md`](./CONFIGURATION.md) · [`PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md) · Contract [`../contracts/inspection_result_v1.json`](../contracts/inspection_result_v1.json)

---

## Grenzen

| | |
|--|--|
| Min. Kameras | **1** |
| Max. Kameras | **4** zertifiziert sequentiell; `AMX_MAX_CAMERAS` bis **16** |
| Treiber heute | OpenCV / V4L2 (USB), **GigE/GenICam (MVP)**, oder Synthetic |
| Capture | **sequentiell** (kein Hardware-Trigger-Sync) |
| GigE / GenICam | ✅ MVP: Discovery + Free-Run/Software-Trigger, 1–4 Kameras |

---

## Ablauf

1. Edge erkennt Geräte: `GET /cameras` (API: `GET /api/v1/cameras`)
2. Admin / Prozessingenieur speichert Auswahl (1–4) unter HMI → Konfiguration  
   oder `PUT /api/v1/cameras/selection` mit `{"camera_ids":[…]}`
3. Inspektion ohne `camera_id` nutzt die Stationsauswahl
4. Pro View: Capture → Infer → Heatmap
5. Gesamtentscheidung = schlechteste Sicht; Top-Level `frame`/`inference` = Worst-View (Kompatibilität)
6. Trend/Drift: `by_camera[]`, `drifting_camera_id`

### Priorität Kamera-Auflösung

1. Request-`camera_ids` (1–4)
2. einzelnes Request-`camera_id` (Legacy / bewusste Einzelkamera)
3. Stationsauswahl (`station_cameras.json`)
4. Fallback `cam-01`

OPC-UA: **leeres** `Inspection.Request.CameraId` → Stationsauswahl (Multi-View).

---

## API (Auszug)

| Methode | Pfad | Zweck |
|---------|------|--------|
| `GET` | `/api/v1/cameras` | Erkannte Kameras + aktuelle Auswahl |
| `GET`/`PUT` | `/api/v1/cameras/selection` | Auswahl lesen / speichern |
| `POST` | `/api/v1/inspections/run` | Case-Lauf (`camera_ids` optional) |
| `GET` | `/api/v1/results/query?camera_id=` | Filter über **jede** View |
| `GET` | `/api/v1/results/trend-summary` | Case-Trend + `by_camera` Drift |
| `GET` | `/api/v1/observability/summary` | inkl. Drift-Felder |
| `GET` | `/api/v1/contracts/inspection-result` | Schema v1.2 + Felderliste |

### Inspektions-Response (Kernfelder)

- `camera_ids`, `view_count`, `views[]`, `decision_policy` (`worst_view`)
- `worst_view_camera_id`
- `trend_warning`, `trend_severity`, `trend_reason`
- `by_camera[]`, `drifting_camera_id`, `drifting_cameras`
- `drift_score`, `score_delta`, `baseline_avg_score`

---

## Drift pro Kamera

Für jede Kamera im Fenster:

- `window_avg_score` vs. `baseline_avg_score`
- `score_delta`, `drift_score`
- `drift_warning` / `severity` / `reason`

Case-Warnung kann auf die **stärkste** Kameradrift angehoben werden (`trend_reason` z. B. `camera_drift:video1:…`).

HMI: Seite **Trends** zeigt die Kamera-Tabelle.

---

## OPC-UA (Contract v1.2)

| Node | Bedeutung |
|------|-----------|
| `Request.CameraId` | leer = Stationsauswahl; gesetzt = Einzelkamera |
| `LastResult.CameraIds` | kommaseparierte IDs |
| `LastResult.ViewCount` | 1–4 |
| `LastResult.WorstViewCameraId` | Sicht mit schlechtester Entscheidung |
| `LastResult.DecisionPolicy` | z. B. `worst_view` |
| `Trend.Warning` / `Severity` / `Reason` | Case-Drift |
| `Trend.DriftingCameraId` | konkrete Kamera |
| `Trend.DriftScore` / `ScoreDelta` | Drift-Metriken |

Details: `opcua-gateway/README.md`, `contracts/opcua_nodeset_mapping_v1.json`.

---

## Deploy (OpenCV, bis 4 Geräte)

```bash
# .env.production
CAMERA_DRIVER=opencv
CAMERA_SOURCE=0
CAMERA_FOURCC=MJPG
CAMERA_WIDTH=3840
CAMERA_HEIGHT=2160
CAMERA_FPS=30
# optional:
# CAMERA_SOURCES_JSON={"video0":"0","video1":"1"}

docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  -f docker-compose.camera.yml --env-file .env.production up -d --build
```

Weitere Host-Geräte in `docker-compose.camera.yml` freischalten (`/dev/video1` …).

## Deploy (GigE / GenICam)

```bash
# .env.production
CAMERA_DRIVER=gige
CAMERA_SOURCE=22345678
# optional:
# CAMERA_SOURCES_JSON={"cam-01":"22345678","cam-02":"CAM-SIDE"}
# CAMERA_TRIGGER=software
# GENICAM_GENTL64_PATH=/opt/gentl

docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  -f docker-compose.gige.yml --env-file .env.production up -d --build
```

Voraussetzungen Host (Ubuntu VPS/IPC):

- Kamera-NIC und Kamera **gleiches L2-Subnetz**
- Jumbo Frames (MTU 9000) auf NIC **und** Kamera, wenn der Switch das unterstützt
- UDP 3956 (GVCP) plus GVSP-Streaming-Ports nicht von UFW/iptables geblockt
- Overlay **nicht** mit `docker-compose.dev.yml` kombinieren (`network_mode: host` vs. `ports`)

Persistenz Auswahl: Volume `api_data` → `/app/data/station_cameras.json`.

## Mehr als 4 Kameras / weitere Linien

- `AMX_MAX_CAMERAS=8` (Hard-Cap 16). HMI liest `max_selectable` von `GET /api/v1/cameras`.
- Zusätzliche Host-Geräte in `docker-compose.camera.yml` bzw. GigE-`CAMERA_SOURCES_JSON`.
- Neue Linie: HMI Vision Setup → **Klonen** oder JSON/YAML-Import (`docs/AI_VISION_EOL_STANDARD.md`).
- IPC: 1 GigE-NIC pro hochauflösender Kamera empfohlen; Jumbo Frames; sequentieller Capture plant die Zykluszeit (`n × grab`).

Ohne gemounteten GenTL-Producer nutzt das Image **Aravis**. Mit `.cti` (Basler pylon, MATRIX VISION, IDS, …) wird Harvesters bevorzugt (`GIGE_BACKEND=auto`).

### Basler (pylon)

1. pylon auf dem Host installieren, Producer `.cti` nach `/opt/gentl` oder `GIGE_GENTL_CTI=…/ProducerGEV.cti`
2. `CAMERA_DRIVER=gige`, `CAMERA_SOURCE=<Serial>` (pylon Viewer)
3. Overlay `docker-compose.gige.yml`, Host-Netz, MTU 9000
4. USB-OpenCV-Kameras bleiben über `CAMERA_DRIVER=opencv` ohne Overlay nutzbar

**Nicht im MVP:** harter Multi-Cam-Hardware-Trigger / Encoder-Sync. `CAMERA_TRIGGER=hardware` setzt GenICam-Nodes best-effort; Linien-Sync bleibt Integrator-Thema.

---

## Go-Live-Checkliste

- [ ] Kameras unter Ubuntu sichtbar (`/dev/video*` **oder** GigE-Discovery `GET /cameras`)
- [ ] Overlay `docker-compose.camera.yml` (USB) **oder** `docker-compose.gige.yml` (GigE) aktiv
- [ ] HMI-Auswahl 1–4 gespeichert
- [ ] Testlauf ohne `camera_id` → `view_count` stimmt
- [ ] OPC-UA Trigger mit leerem CameraId → Multi-View
- [ ] Trends: `by_camera` / driftende Kamera nachvollziehbar
- [ ] Bei bewegtem Teil: Sync-Konzept (Hardware) geklärt
