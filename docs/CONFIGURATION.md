# AnomalyMatrix — Konfiguration

Stand: **v1.2.0** (Multi-Kamera Case-Prüfung + Per-Camera-Drift)

Diese Anleitung folgt **nach** der Installation (`docs/INSTALLATION.md`).  
Ziel: aus einem laufenden Stack ein **linienfähiges** System machen.

---

## 1. Erster Login (HMI)

1. Browser: `http://<HOST>/` (mit TLS: `https://<HOST>/`)
2. Benutzer: `admin-1`
3. Passwort: aus `CREDENTIALS.txt` bzw. `AMX_ADMIN_PASSWORD`
4. Nach Login: Dashboard → **Run** (Smoke-Inspektion)

API-Check:

```bash
curl -fsS http://127.0.0.1:8080/api/v1/health
curl -fsS http://127.0.0.1:8080/api/v1/ready
```

`/ready` muss `status: ready` liefern (Postgres + Edge erreichbar).

---

## 2. Umgebungsvariablen (Produktion)

Datei: `.env.production` (Vorlage: `.env.production.example`)

| Variable | Pflicht | Bedeutung |
|----------|---------|-----------|
| `ANOMALYMATRIX_ENV` | ja | `prod` |
| `JWT_SECRET` | ja | ≥32 Zeichen |
| `SERVICE_AUTH_TOKEN` | ja | ≥24 Zeichen, API↔Edge↔Gateway |
| `LICENSE_ADMIN_TOKEN` | ja | Lizenz-Admin-Aktionen |
| `LICENSE_SERVER_URL` | empfohlen Prod | Byte-Commander License Server |
| `LICENSE_PRODUCT_ID` | mit Server | Integer-Product-ID |
| `AMX_CORS_ORIGINS` | ja | HMI-URL(s), kommagetrennt |
| `AMX_ADMIN_PASSWORD` | erstes Setup | Bootstrap Admin-Login |
| `COOKIE_SECURE` | ja bei HTTPS | `true` hinter TLS |
| `DATABASE_URL` / `POSTGRES_*` | ja | Postgres |
| `OPCUA_API_KEY` | ja | muss `users.api_key` von `operator-1` sein |
| `OPCUA_SECURITY_ENABLED` | ja in Prod | `true` |
| `EDGE_ACQUISITION_URL` | ja | z. B. `http://edge-acquisition:8091` |
| `ANOMALYMATRIX_INFERENCE_PROVIDER` | ja | `patchcore` (nicht `stub`) |
| `CAMERA_DRIVER` | empfohlen | `synthetic`, `opencv` oder `gige` (`genicam`) |
| `CAMERA_SOURCE` | bei opencv/gige | Index, `/dev/video*`, Datei **oder** GigE-Serial / User-Name / GenTL-ID |
| `CAMERA_SOURCES_JSON` | optional | Mapping `camera_id → source` (1–N, Default-Max 4, `AMX_MAX_CAMERAS`) |
| `MQTT_ENABLED` / `MQTT_BROKER` / `MQTT_TOPIC` | optional | MQTT-Trigger (zusätzlich zu OPC-UA) |
| `AMX_STATION_ID` | empfohlen | Stations-ID in Object-Keys und Vision-Profil |
| `AMX_MAX_CAMERAS` | optional | >4 bis 16; zertifizierter sequentieller Pfad bleibt 1–4 |
| `AMX_RETENTION_TTL_DAYS` | empfohlen | Lösch-/Archivfrist Rohbilder (Default 90) |
| `MINIO_PUBLIC_BASE` | empfohlen | `/artifacts` (HMI-Heatmaps) |
| `INFLUX_*` / `MINIO_*` | empfohlen | Metriken / Artefakte |

Installer erzeugt die Secrets automatisch. Manuell: alle `REPLACE_*` ersetzen.

Nach Änderung:

```bash
cd /opt/anomalymatrix   # oder Repo-Pfad
docker compose -p anomalymatrix -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production up -d
```

---

## 3. TLS / HTTPS

Ohne TLS bleiben Session-Cookies hinter HTTP unsicher (`COOKIE_SECURE`).

### Variante A — Installer

```bash
sudo ./scripts/install.sh --mode prod --host <HOST> --tls
```

Setzt `COOKIE_SECURE=true`. TLS-Terminierung weiterhin nötig (Proxy/Caddy).

### Variante B — Compose-Overlay

```bash
mkdir -p certs
# tls.crt + tls.key ablegen
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.tls.yml \
  --env-file .env.production up -d
```

Caddy-Config: `infra/caddy/Caddyfile`  
`AMX_CORS_ORIGINS` auf `https://<HOST>` setzen.

---

## 4. Kamera

Default Install: `CAMERA_DRIVER=synthetic` (ohne Host-Kamera).

### OpenCV-Webcam / V4L2

```bash
# in .env.production
CAMERA_DRIVER=opencv
CAMERA_SOURCE=0
# optional: CAMERA_DEVICE=/dev/video0

docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.camera.yml \
  --env-file .env.production up -d --build edge-acquisition
```

Datei als Quelle: `CAMERA_SOURCE=/path/to/image.png` (im Container erreichbar mounten).

### Multi-Kamera (gleicher Case, 1–4)

- Hardware-Erkennung: `GET /api/v1/cameras` (Edge: `GET /cameras`)
- Auswahl speichern: `PUT /api/v1/cameras/selection` — Body `{"camera_ids":["video0","video1"]}`  
  Rollen: Admin / Prozessingenieur (HMI → Konfiguration)
- Grenzen: **min. 1**, **max. 4** zertifiziert sequentiell (`AMX_MAX_CAMERAS` bis 16)
- Inspektion nutzt die gespeicherte Auswahl; Entscheidung: **worst view wins**
- Override pro Request: `POST /api/v1/inspections/run` mit `camera_ids`
- OPC-UA: leeres `Request.CameraId` → Stationsauswahl; `LastResult` liefert `CameraIds`, `ViewCount`, `WorstViewCameraId`
- Drift: `GET /results/trend-summary` enthält `by_camera[]`, `drifting_camera_id`, `drift_score`, `score_delta`
- Mehrere Host-Geräte in `docker-compose.camera.yml` freischalten; optional  
  `CAMERA_SOURCES_JSON='{"video0":"0","video1":"1"}'`

> Hinweis: Capture ist derzeit **sequentiell** (kein Hardware-Trigger-Sync). Für bewegte Teile Sync separat planen.

### GigE Vision / GenICam (MVP)

Bevorzugter Pfad für industrielle Bildqualität (vor RTSP). Stack:

- **Aravis 0.8** (open GigE Vision, im Edge-Image) — ohne Vendor-SDK
- **Harvesters 1.4 + GenTL `.cti`**, wenn ein Hersteller-Producer gemountet ist (`GENICAM_GENTL64_PATH` / `GIGE_GENTL_CTI`)

```bash
# in .env.production
CAMERA_DRIVER=gige
CAMERA_SOURCE=22345678
# optional Multi-Cam:
# CAMERA_SOURCES_JSON={"cam-01":"22345678","cam-02":"CAM-SIDE"}
# CAMERA_EXPOSURE_MS=8
# CAMERA_GAIN_DB=0
# CAMERA_TRIGGER=software
# GIGE_BACKEND=auto

docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.gige.yml \
  --env-file .env.production up -d --build edge-acquisition api
```

**Host-Netz** ist Pflicht (GVCP UDP 3956 + Streaming). Jumbo Frames: `sudo ip link set <cam-nic> mtu 9000`.  
Details: `edge-acquisition/README.md`, Overlay `docker-compose.gige.yml`.

Einschränkungen MVP: ein Frame pro Capture-Aufruf; Hardware-Line/Encoder-Sync nur best-effort (`CAMERA_TRIGGER=hardware`); kein getesteter Multi-Cam-Sync über I/O. Getesteter Open-Stack: Aravis 0.8 auf Debian Bookworm. Vendor-CTI (pylon, mvGenTL, IDS peak, …) hängt vom gemounteten Producer ab.

---

## 5. OPC-UA / SPS

### NodeIds (Contract)

Mapping: `contracts/opcua_nodeset_mapping_v1.json`  
Nodes nutzen String-IDs, z. B. `ns=2;s=Inspection.Busy`.

Details: `opcua-gateway/README.md`

### Kunden-PKI (statt Self-Signed)

1. PEMs als `server_cert.pem` / `server_key.pem` ins Volume `opcua_certs` legen  
   oder `OPCUA_SERVER_CERT` / `OPCUA_SERVER_KEY` setzen  
2. Vorhandene Dateien werden **nicht** überschrieben  
3. SPS: Trust auf Server-Zertifikat + Sign/Encrypt (Basic256Sha256)

### API-Key

Gateway sendet `X-AMX-Api-Key: $OPCUA_API_KEY`.  
Installer synced den Key auf User `operator-1` in Postgres (hard-fail bei Fehler).

Manuell prüfen:

```bash
docker compose … exec -T postgres \
  psql -U anomaly -d anomalymatrix -c \
  "SELECT user_id, left(api_key,8) FROM users WHERE user_id='operator-1';"
```

### Trigger-Test

- SPS: Flanke auf `Inspection.ExternalTrigger` oder `StartRequest` (optional `Request.Epc`)
- oder HTTP (mit Service-Token): `POST http://opcua-gateway:8092/trigger`
- MQTT: Topic `anomalymatrix/eol/trigger` mit JSON `{"action":"inspect","epc":"..."}`  
  Overlay: `docker-compose.mqtt.yml`. Commissioning ohne Broker: `POST /api/v1/triggers/mqtt`

AI-Vision-EOL-Standard (Vision Setup, Retention, Watchdog): [`AI_VISION_EOL_STANDARD.md`](./AI_VISION_EOL_STANDARD.md)

---

## 6. Rezepte, Modelle, Training

HMI → **Configuration** → Abschnitt **Training / Modelle**.

Nur **i.O.-Gutteile** ins Training geben. Das System lernt den Sollzustand.

**QA „Anomalie bestätigt“** ist der n.i.O.-Pfad: die Prüfung wird in Liste und Detail **n.i.O. (rot)** angezeigt, das Bild landet unter `data/nio-images/{recipe_id}/` (nicht in der Gutteil-Memory-Bank). Falsch positiv und Nachprüfung ändern die Ampel nicht auf n.i.O.

Ablauf in der HMI:

1. Rezept wählen, Kamera in der Kamerauswahl setzen (Live: USB OpenCV `/dev/video0`). Status (erreichbar/offline) steht im Dashboard und unter Configuration.
2. **Gutteile erfassen** — speichert PNG unter `data/training-images/{recipe_id}/` (und optional MinIO `raw-images`).
3. **Training starten** — erzeugt einen Kandidaten (`status=candidate`) und eine Memory-Bank `.npz` unter `training-artifacts/`. Vorherige Artefakte bleiben liegen. Bestätigte n.i.O.-Muster erscheinen als Holdout in den Trainings-Metadaten.
4. Nach Prüfung **Promoten** (Validierung) oder **Aktivieren** (gespeichertes Training ohne Neu-Training).
5. **Rollback** oder ein älteres Training aus der Historie erneut aktiv setzen. `active_memory_bank.npz` zeigt dann auf das gewählte Artefakt.
6. **Entscheidungsschwellen** (Configuration, Engineer/Admin): Nachprüfung / n.i.O. je Rezept, Standard 0,55 / 0,85.
7. **Rezepte** (Configuration): Prozessingenieur/Admin legen Rezepte an, ändern Name/Version/Kamera-/Lichtprofil/Schwellen und setzen das aktive Rezept. Operatoren lesen und wählen das Rezept am Dashboard.
8. Dashboard **Inspektion starten** → Score, i.O./n.i.O., Modellversion, Memory-Bank-Status.
9. Inspection Detail **QA-Feedback**: Anomalie bestätigt → n.i.O. + Muster; Falsch positiv → keine n.i.O.-Markierung; Nachprüfung bleibt offen.

| Aktion | Endpoint / Ort |
|--------|----------------|
| Rezepte lesen | `GET /api/v1/recipes` (Operator/Engineer/Admin) |
| Rezept anlegen | `POST /api/v1/recipes` (Engineer/Admin) |
| Rezept ändern | `PUT /api/v1/recipes/{id}` (Engineer/Admin) |
| Rezept löschen | `DELETE /api/v1/recipes/{id}` mit `{confirm:true, confirm_recipe_id}` (Engineer/Admin, **doppelte Bestätigung**) |
| Schwellen speichern | `PUT /api/v1/recipes/{id}/thresholds` (Engineer/Admin) |
| Modelle + Historie + Memory-Bank + n.i.O.-Zähler | `GET /api/v1/models` |
| Gutteile erfassen | `POST /api/v1/models/training-samples` (Engineer/Admin) |
| Trainieren | `POST /api/v1/models/train` (Engineer/Admin) |
| Promoten | `POST /api/v1/models/{id}/promote` |
| Gespeichertes Training aktivieren | `POST /api/v1/models/{id}/activate` |
| Rollback | `POST /api/v1/models/rollback` |
| QA-Feedback | `POST /api/v1/feedback` (`confirm_anomaly` / `false_positive` / `needs_review`) |

Rechte: `recipes.write` / `models.train` / `models.promote` (Prozessingenieur, Admin). Operatoren haben `recipes.read` und `models.read` (Historie sichtbar, Aktionen deaktiviert).

**Rezept löschen (sicheres Default):**

- HMI verlangt **zwei Schritte**: „Wirklich löschen?“ und „Endgültig löschen — nicht rückgängig“ inkl. Eingabe der Rezept-ID.
- API verlangt denselben Schutz: `DELETE` mit `{ "confirm": true, "confirm_recipe_id": "<id>" }`.
- `recipe-default` ist **geschützt** und kann nicht gelöscht werden (System-Fallback für Inspektion, OPC-UA, MQTT/EOL).
- Löschen wird **blockiert**, solange ein Modell mit Status `active` oder `candidate` das Rezept in `metadata.recipe_id` referenziert. Zuerst anderes Modell promoten/aktivieren.
- Das letzte verbleibende Rezept kann nicht gelöscht werden.
- Gutteil-Ordner `training-images/{id}` und n.i.O.-Ordner `nio-images/{id}` werden nach `archived-recipes/{id}/{timestamp}/` **verschoben**, nicht mitgelöscht.
- Historische Inspektionen bleiben erhalten (`recipe_id` ist ein String, kein FK).
- War das gelöschte Rezept aktiv, wird `recipe-default` (sonst das nächste vorhandene) aktiv gesetzt.

Provider in Prod: `ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore`.  
Training braucht Gut-Teil-Bilder (`training-images/{recipe_id}` hat Vorrang vor MinIO `raw-images`). Ohne Memory Bank fällt die Inferenz auf OpenCV/Hash zurück; die Heatmap ist dann ein **Kanten-Residual** (im HMI als Nicht-Modell gekennzeichnet).

**Heatmap:** Neue Trainings speichern ein **Patch-Gitter** (16×16) in der Memory Bank. Die Overlay-Karte ist der min. Embedding-Abstand je Patch — Hotspots liegen auf der Defektregion, nicht auf allen Kanten. Ältere bildweite Banken (`layout=image`, ein 32×32-Vektor je Gutteil) bleiben ladbar und erzeugen ein Residual zum nächsten Gutteil-Embedding. Für korrekte Patch-Lokalisierung **einmal neu trainieren und promoten**.

---

## 7. Lizenz

Mit `LICENSE_SERVER_URL` + `LICENSE_PRODUCT_ID` (Integer) gegen den
[Byte-Commander License Server](https://github.com/TheRealByteCommander/software-licensing-concept).
Ohne Server-URL: Installer-Bootstrap (`AMX-INSTALL-…` in `CREDENTIALS.txt`).
Details: [`LICENSE_INTEGRATION.md`](./LICENSE_INTEGRATION.md).

| Aktion | Header / Hinweis |
|--------|------------------|
| Status | `GET /api/v1/license/status` (auth) |
| Activate/Deactivate | RBAC **und** `X-License-Admin-Token` |

Siehe `docs/OPS_LICENSE_RUNBOOK.md`, `docs/LICENSE_INTEGRATION.md`.

---

## 8. Benutzer & Rollen

Seed-User (Postgres/`users`):

| user_id | Rolle |
|---------|--------|
| `admin-1` | admin |
| `operator-1` | operator (OPC-UA-API-Key) |
| `qa-1` | qa_lead |
| `engineer-1` | process_engineer |

In Prod: **keine** Dev-Header (`X-AMX-Role`). Login über HMI oder JWT/API-Key.

Seed-API-Keys `amx-key-*` nach Install rotiert — nicht wiederverwenden.

---

## 9. Backup & Restore

```bash
cd /opt/anomalymatrix
MODE=prod ./scripts/backup/backup.sh
MODE=prod ./scripts/backup/restore.sh backups/<timestamp>
```

Nutzt `docker compose exec` gegen den Postgres-Container (kein Host-Port nötig).

---

## 10. Go-Live-Checkliste

- [ ] `/api/v1/health` und `/api/v1/ready` grün  
- [ ] HMI-Login mit Admin  
- [ ] Smoke-Inspektion im Dashboard  
- [ ] TLS aktiv, `COOKIE_SECURE=true`, CORS = HTTPS-URL  
- [ ] OPC-UA: Kunden-Zertifikate, SPS-Trigger + Ergebnis-Nodes  
- [ ] Kamera: `opencv` / `gige` **oder** bewusst synthetic für Demo  
- [ ] Multi-Kamera: Auswahl 1–4 gespeichert; Testlauf `view_count` ok (`docs/MULTI_CAMERA.md`)  
- [ ] MQTT (optional): Overlay `docker-compose.mqtt.yml`, Topic `anomalymatrix/eol/trigger`, EPC im Payload  
- [ ] Vision Setup: Kamerarollen inkl. Unteransicht, Checkliste bestätigt, Vorlage exportiert  
- [ ] Retention/Watchdog: `GET /storage/stats`, Self-Test nach Reboot  
- [ ] Drift: `trend-summary.by_camera` / `drifting_camera_id` nachvollziehbar  
- [ ] `OPCUA_API_KEY` = `operator-1.api_key`  
- [ ] PatchCore-Modell trainiert/promoted (falls Live-Linie)  
- [ ] Backup getestet  
- [ ] `CREDENTIALS.txt` ins Vault, Datei löschen/verschlüsseln  

Freigabe-Status: `docs/RELEASE_READINESS.md`  
Betrieb: `docs/PRODUCTION_RUNBOOK.md`
