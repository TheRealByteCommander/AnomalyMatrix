# AnomalyMatrix — AI-Vision EOL-Standard (Software-Referenz)

Stand: additiv zu **v1.2.0**. Physische Optik (Objektivkauf, Leuchtenwahl vor Ort) bleibt eine Inbetriebnahme-Entscheidung — die Plattform liefert dafür **konfigurierbare Standards, Checklisten, Capture-Profile und messbare Abnahmekriterien**.

Verwandt: [`CONFIGURATION.md`](./CONFIGURATION.md) · [`PRODUCTION_RUNBOOK.md`](./PRODUCTION_RUNBOOK.md) · [`MULTI_CAMERA.md`](./MULTI_CAMERA.md) · Contracts in `contracts/`

---

## Reviewer-Checkliste (Phase 1–3, software-relevant)

### Foundations
- [ ] IPC-Netzbetrieb: Compose `restart: unless-stopped` + systemd/LXC-Onboot (`scripts/systemd/`, `scripts/lxc/onboot.sh`)
- [ ] Auto-Recovery: Healthchecks, MQTT-Reconnect, Retention-Loop, `/api/v1/system/self-test`
- [ ] Basler / GigE / GenICam: `CAMERA_DRIVER=gige` + Overlay `docker-compose.gige.yml` (USB/OpenCV bleibt)
- [ ] MQTT-Trigger **und** OPC-UA-Trigger (beide aktivierbar, unabhängig)
- [ ] EPC über MQTT / OPC-UA / API, an jedes Capture gebunden, in HMI und Metadaten
- [ ] MinIO/S3: strukturierte Keys, Retention/Archiv/Löschen, Legal-Hold, documented ACLs

### Phase 1
- [ ] HMI Konfiguration → **EOL-Stationsstandard / Vision Setup**
- [ ] Kameras 1–N, Rollen top/side/bottom/STF/completeness
- [ ] Objektiv-/FOV-Notizen, Belichtung/Gain/Trigger, Light-Controller-Hook
- [ ] Perspektiv-Checkliste (Ecken/Kanten/Merkmale/Unteransicht) mit Operator-Bestätigung
- [ ] Export JSON/YAML, Import, Klon für andere Linien
- [ ] Empfehlungen aus Profil + Capture-Statistik (Format, Auflösung, Mono/RGB)

### Phase 2
- [ ] `POST /api/v1/triggers/mqtt` bzw. Broker-Topic startet Inspektion
- [ ] EPC eindeutig am Image-Set (`epc_binding`, Sidecar-JSON)
- [ ] Object-Key: `station/recipe/epc/yyyy/mm/dd/<ts>_<cam>_<decision>_image.ext`
- [ ] PNG/JPEG je Kameraprofil; RAW-Passthrough wenn Driver `raw_bytes` liefert, sonst dokumentierte Limitation
- [ ] Auflösung / Mono-RGB je Slot
- [ ] `GET /api/v1/storage/stats` + HMI-Panel
- [ ] Retention TTL / Archiv-Bucket / Legal-Hold
- [ ] Watchdog + Gap-Detection in HMI (≥24h-Ausdauer)
- [ ] Self-Test nach Reboot

### Phase 3
- [ ] Multi-Cam 1–4 zertifiziert sequentiell; `AMX_MAX_CAMERAS` bis 16
- [ ] Versionierte Contracts: ImageAsset, CaptureSet, EpcBinding, StationVisionProfile, RetentionPolicy
- [ ] Wizard: Clone/Export/Import in der HMI

Bestehende Flows bleiben: HMI-Inspektion, PatchCore train/promote/activate, QA confirm→n.i.O., OPC-UA Gateway, Lizenz, MinIO, Schwellen, DE/EN.

---

## Trigger (MQTT + OPC-UA)

| Quelle | Wie |
|--------|-----|
| OPC-UA | Flanke `Inspection.ExternalTrigger` / `StartRequest` / Method `StartInspection` |
| MQTT | Topic `MQTT_TOPIC` (Default `anomalymatrix/eol/trigger`), JSON-Payload |
| API / HMI | `POST /api/v1/inspections/run` |
| Commissioning | `POST /api/v1/triggers/mqtt` (ohne Broker) |

Beispiel MQTT:

```json
{
  "action": "inspect",
  "epc": "urn:epc:id:sgtin:0614141.107346.2017",
  "process_id": "WO-4412",
  "recipe_id": "recipe-default"
}
```

`action: capture` speichert den Bildsatz ohne Inferenz. OPC-UA bleibt unverändert nutzbar.

Nodes: `Inspection.Request.Epc`, `Inspection.Request.ProcessId`, `Inspection.LastResult.Epc`.

---

## Datensatz / Speicher

Object-Key:

```
{station_id}/{recipe_id}/{epc}/{yyyy}/{mm}/{dd}/{timestamp}_{camera_id}_{decision}_image.{png|jpeg|raw}
```

Sidecar `*.json` = ImageAsset (EPC, Kamera, Format, Legal-Hold). CaptureSet hängt am Inspektions-DTO.

Retention: `AMX_RETENTION_TTL_DAYS` (Default 90), Archiv-Bucket `archive-images`, optionales Legal-Hold. MinIO-Lifecycle wird gesetzt, wenn TTL konfiguriert ist. Raw-Images sind **privat** (kein Public-Get); Heatmaps bleiben HMI-lesbar über `/artifacts/`.

---

## Kameras & Basler

- USB/OpenCV: `CAMERA_DRIVER=opencv` + `docker-compose.camera.yml`
- GigE/GenICam (Basler pylon CTI oder Aravis): `CAMERA_DRIVER=gige` + `docker-compose.gige.yml`
- Basler: `GENICAM_GENTL64_PATH` auf pylon Producer, `CAMERA_SOURCE=<serial>`, Jumbo Frames MTU 9000, Host-Netz
- Mehr als 4 Slots: `AMX_MAX_CAMERAS=8` (Hard-Cap 16). Sequentieller Capture bleibt; Hardware-Sync ist Integrator-Thema (dokumentiert).

---

## Abnahme (software)

1. Self-Test: `POST /api/v1/system/self-test`
2. Checkliste im HMI abhaken (Ecken/Kanten/Merkmale/Unteransicht)
3. MQTT- oder OPC-UA-Trigger mit EPC → Inspektion in Recent + Detail
4. `GET /api/v1/storage/stats` zeigt Bytes/Count
5. Retention-Trockenlauf: `POST /api/v1/storage/retention/run`
6. 24h: Watchdog ohne anhaltende `gap`-Stürme (Intervall `AMX_CAPTURE_WATCHDOG_SEC`)

Optik vor Ort: Objektiv/Beleuchtung gemäß Slot-Notizen und Empfehlungsmodul kaufen und in der Checkliste bestätigen — nicht „out of scope“.
