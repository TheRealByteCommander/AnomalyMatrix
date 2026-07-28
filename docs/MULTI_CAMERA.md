# Multi-Kamera Case-Prüfung & Drift

Stand: **v1.2.0** (Branch / nach Merge von Multi-View)

Mehrere Kameras (Hardware-erkannt) prüfen **denselben Case**. Ergebnis-Aggregation: **worst view wins**. Drift wird **pro Kamera** ausgewiesen.

Verwandt: [`CONFIGURATION.md`](./CONFIGURATION.md) · [`PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md) · Contract [`../contracts/inspection_result_v1.json`](../contracts/inspection_result_v1.json)

---

## Grenzen

| | |
|--|--|
| Min. Kameras | **1** |
| Max. Kameras | **4** |
| Treiber heute | OpenCV / V4L2 (USB) oder Synthetic |
| Capture | **sequentiell** (kein Hardware-Trigger-Sync) |
| GigE / GenICam | Folgerelease |

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
# optional:
# CAMERA_SOURCES_JSON={"video0":"0","video1":"1"}

docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  -f docker-compose.camera.yml --env-file .env.production up -d --build
```

Weitere Host-Geräte in `docker-compose.camera.yml` freischalten (`/dev/video1` …).

Persistenz Auswahl: Volume `api_data` → `/app/data/station_cameras.json`.

---

## Go-Live-Checkliste

- [ ] Kameras unter Ubuntu als `/dev/video*` sichtbar
- [ ] Overlay `docker-compose.camera.yml` aktiv
- [ ] HMI-Auswahl 1–4 gespeichert
- [ ] Testlauf ohne `camera_id` → `view_count` stimmt
- [ ] OPC-UA Trigger mit leerem CameraId → Multi-View
- [ ] Trends: `by_camera` / driftende Kamera nachvollziehbar
- [ ] Bei bewegtem Teil: Sync-Konzept (Hardware) geklärt
