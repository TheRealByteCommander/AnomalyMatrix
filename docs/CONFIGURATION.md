# AnomalyMatrix — Konfiguration

Stand: **v1.1.x** (Multi-Kamera Case-Prüfung + Per-Camera-Drift)

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
| `CAMERA_DRIVER` | empfohlen | `synthetic` oder `opencv` |
| `CAMERA_SOURCE` | bei opencv | `0`, `/dev/video0` oder Bilddatei |
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
- Grenzen: **min. 1**, **max. 4** Kameras
- Inspektion nutzt die gespeicherte Auswahl; Entscheidung: **worst view wins**
- Override pro Request: `POST /api/v1/inspections/run` mit `camera_ids`
- OPC-UA: leeres `Request.CameraId` → Stationsauswahl; `LastResult` liefert `CameraIds`, `ViewCount`, `WorstViewCameraId`
- Drift: `GET /results/trend-summary` enthält `by_camera[]`, `drifting_camera_id`, `drift_score`, `score_delta`
- Mehrere Host-Geräte in `docker-compose.camera.yml` freischalten; optional  
  `CAMERA_SOURCES_JSON='{"video0":"0","video1":"1"}'`

> Hinweis: Capture ist derzeit **sequentiell** (kein Hardware-Trigger-Sync). Für bewegte Teile Sync separat planen.

GigE/GenICam: noch nicht enthalten (Folgerelease).

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

- SPS: Flanke auf `Inspection.ExternalTrigger` oder `StartRequest`  
- oder HTTP (mit Service-Token): `POST http://opcua-gateway:8092/trigger`

---

## 6. Rezepte, Modelle, Training

HMI → **Configuration** zeigt aktives Rezept/Modell (API).

| Aktion | Endpoint / Ort |
|--------|----------------|
| Rezepte lesen | `GET /api/v1/recipes` |
| Modelle lesen | `GET /api/v1/models` |
| Trainieren | `POST /api/v1/models/train` (Engineer/Admin) |
| Promoten | `POST /api/v1/models/{id}/promote` |
| Rollback | `POST /api/v1/models/rollback` |

Provider in Prod: `ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore`.  
Training braucht Gut-Teil-Bilder (MinIO `raw-images` und/oder lokal).

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
- [ ] Kamera: `opencv` + Gerät **oder** bewusst synthetic für Demo  
- [ ] Multi-Kamera: Auswahl 1–4 gespeichert; Testlauf `view_count` ok (`docs/MULTI_CAMERA.md`)  
- [ ] Drift: `trend-summary.by_camera` / `drifting_camera_id` nachvollziehbar  
- [ ] `OPCUA_API_KEY` = `operator-1.api_key`  
- [ ] PatchCore-Modell trainiert/promoted (falls Live-Linie)  
- [ ] Backup getestet  
- [ ] `CREDENTIALS.txt` ins Vault, Datei löschen/verschlüsseln  

Freigabe-Status: `docs/RELEASE_READINESS.md`  
Betrieb: `docs/PRODUCTION_RUNBOOK.md`
