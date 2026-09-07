# edge-acquisition

HTTP Capture-Service für AnomalyMatrix.

## Funktion
- `GET /cameras` — Hardware-Erkennung (V4L2/OpenCV, GigE/GenICam oder Synthetic)
- `POST /capture` — Frame + Metadaten (`camera_id`, optional `source`)
- Wird von der API über `EDGE_ACQUISITION_URL` angesprochen

## Treiber (`CAMERA_DRIVER`)

| Wert | Bedeutung |
|------|-----------|
| `synthetic` | Default, keine Hardware |
| `opencv` (Aliases: `webcam`, `file`, `real`) | USB/V4L2, Index, `/dev/video*`, Standbild |
| `gige` (Aliases: `genicam`, `gigE`) | GigE Vision / GenICam |

## Multi-Kamera
Bis zu 4 Geräte. Mapping optional über `CAMERA_SOURCES_JSON`.  
Auswahl und Same-Case-Aggregation liegen in der API (`/api/v1/cameras*`, Inspektion).

Capture ist **sequentiell** (ein Frame pro `/capture`-Aufruf). Hardware-Trigger-Sync / Encoder ist vorbereitet (GenICam-Nodes `TriggerMode` / `TriggerSource`) aber kein voller Linien-Sync — siehe unten.

## Port
**8091** (Docker Compose: `edge-acquisition:8091`; mit GigE-Overlay auf dem Host)

## Lokal starten
```bash
pip install -r requirements.txt
uvicorn service:app --host 0.0.0.0 --port 8091
```

Backend `.env`: `EDGE_ACQUISITION_URL=http://127.0.0.1:8091`

---

## GigE Vision / GenICam (MVP)

Zwei Backends, automatisch (`GIGE_BACKEND=auto`):

1. **Harvesters + GenTL-Producer** (`.cti`), wenn `GENICAM_GENTL64_PATH` oder `GIGE_GENTL_CTI` gesetzt ist — portable GenICam, herstellerabhängig.
2. **Aravis** (open GigE Vision, im Docker-Image enthalten) — kein Vendor-SDK, GVCP/GVSP direkt. Getestet gegen **Aravis 0.8** (Debian Bookworm `libaravis-0.8` + `gir1.2-aravis-0.8`).

Ohne Producer **und** ohne Aravis schlägt `/capture` mit einer klaren 503-Meldung fehl; `GET /cameras` liefert `cameras: []` plus `error`.

### Geräteauswahl

`CAMERA_SOURCE` / `CAMERA_SOURCES_JSON` / Request-`source` akzeptieren:

- Seriennummer
- GenICam `DeviceUserID` (User-defined name)
- GenTL-/Aravis-Geräte-ID
- optional Prefix: `serial:`, `user:`, `id:`, `ip:`

Beispiel:

```bash
CAMERA_DRIVER=gige
CAMERA_SOURCE=22345678
CAMERA_SOURCES_JSON='{"cam-01":"22345678","cam-02":"CAM-SIDE"}'
CAMERA_EXPOSURE_MS=8
CAMERA_GAIN_DB=0
CAMERA_TRIGGER=software   # freerun | software | hardware
```

`CAMERA_TRIGGER=hardware` setzt best-effort `TriggerSource` (`CAMERA_TRIGGER_SOURCE`, Default `Line1`). **Encoder-/Multi-Cam-Hardware-Sync ist Folgerelease** — das Interface blockiert ihn nicht.

### Docker (VPS / Ubuntu)

```bash
CAMERA_DRIVER=gige \
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  -f docker-compose.gige.yml --env-file .env.production up -d --build
```

Das Overlay nutzt **`network_mode: host`** (GigE-Discovery/Streaming funktionieren nicht zuverlässig hinter Docker-NAT). Die API erreicht Edge über `host.docker.internal:8091`.

NIC auf dem **Host**:

- Kamera und IPC in **einem Subnetz** (kein Routing/NAT dazwischen)
- Jumbo Frames empfohlen: `sudo ip link set <nic> mtu 9000` (Kamera-MTU analog)
- GVCP **UDP 3956**, GVSP hohe UDP-Ports; Firewall nicht blocken
- `8091/tcp` ist mit Host-Netz auf dem Host sichtbar — per UFW auf Docker-Bridge/Localhost beschränken

Optional Vendor-CTI mounten (Harvesters), siehe Kommentare in `docker-compose.gige.yml`.

### Tests

```bash
cd edge-acquisition
pip install -r requirements.txt pytest
PYTHONPATH=. pytest -q
```

CI mockt GenTL/Harvesters; es wird **keine** echte Kamera benötigt.
