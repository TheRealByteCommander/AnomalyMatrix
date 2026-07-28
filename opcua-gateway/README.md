# opcua-gateway

OPC-UA-Gateway für AnomalyMatrix (**v1.1.x**) — SPS-Anbindung, Sign/Encrypt, Multi-View LastResult + Drift-Nodes.

## Funktion
- **asyncua** OPC-UA-Server (Port **4840**)
- **PLC → AnomalyMatrix:** automatische Inspektion per Trigger oder Methode
- **AnomalyMatrix → PLC:** Ergebnis, Stop-Linie, Ausschleusen bei rot
- **Multi-View:** leeres `Request.CameraId` → Stationsauswahl (1–4 Kameras)
- Node-Mapping: `contracts/opcua_nodeset_mapping_v1.json` (v1.2, String-NodeIds `ns=2;s=…`)

## Ports
| Port | Protokoll |
|------|-----------|
| 8092 | HTTP (FastAPI; in Prod ohne OpenAPI, Service-Token Pflicht) |
| 4840 | OPC-UA |

## Sicherheit / PKI
- Prod: `OPCUA_SECURITY_ENABLED=true` (Basic256Sha256 Sign/Encrypt)
- Zertifikate unter `OPCUA_CERT_DIR` (Compose-Volume `opcua_certs`)
- Vorhandene `server_cert.pem` / `server_key.pem` werden **nicht** überschrieben
- Optional: `OPCUA_SERVER_CERT` / `OPCUA_SERVER_KEY` auf Kunden-PEMs zeigen

Siehe `docs/CONFIGURATION.md` (Abschnitt OPC-UA) und `docs/PRODUCTION_RUNBOOK.md`.


## PLC-Schnittstelle (Überblick)

### Eingänge (SPS schreibt)
| Node | Typ | Funktion |
|------|-----|----------|
| `Inspection.ExternalTrigger` | Boolean | Flanke → Inspektion starten |
| `Inspection.StartRequest` | Boolean | Alternative Trigger-Flanke |
| `Inspection.Request.CameraId` | String | Kamera-Override; **leer** = Stations-Multi-View |
| `Inspection.Request.RecipeId` | String | Rezept (optional) |
| `Inspection.AcknowledgeStop` | Boolean | Quittiert Stop — löscht `StopLineRequest` |

### Ausgänge (AnomalyMatrix schreibt)
| Node | Typ | Funktion |
|------|-----|----------|
| `Inspection.Busy` | Boolean | Inspektion läuft |
| `Inspection.ResultReady` | Boolean | Neues Ergebnis verfügbar |
| `Inspection.StopLineRequest` | Boolean | **TRUE bei rot** → Linie stoppen |
| `Inspection.RejectPart` | Boolean | **TRUE bei rot** → Teil ausschleusen |
| `LastResult.DecisionCode` | Int32 | 0=grün, 1=gelb, 2=rot |
| `LastResult.PassFailBool` | Boolean | TRUE nur bei grün |
| `LastResult.CameraIds` | String | kommaseparierte View-IDs |
| `LastResult.ViewCount` | Int32 | 1–4 |
| `LastResult.WorstViewCameraId` | String | schlechteste Sicht |
| `LastResult.DecisionPolicy` | String | z. B. `worst_view` |
| `LastResult.*` | diverse | Score, ID, DefectClass, … |
| `Trend.Warning` / `Severity` / `Reason` | | Case-Drift |
| `Trend.DriftingCameraId` | String | konkrete Drift-Kamera |
| `Trend.DriftScore` / `ScoreDelta` | Double | Drift-Metriken |
| `System.State` | String | ready / busy / error |

### Methode
- `Inspection.StartInspection(CameraId, RecipeId)` → Boolean Erfolg  
  (`CameraId=""` → Multi-View Stationsauswahl)

Siehe auch `docs/MULTI_CAMERA.md`.

## HTTP-API (Gateway)
- `GET /health` — Status
- `GET /contract` — NodeSet JSON
- `POST /publish` — Nodes setzen (von Backend nach Inspektion)
- `POST /trigger` — manueller Trigger-Test
- `GET /nodes` — aktuelle Werte

## Umgebungsvariablen
| Variable | Zweck |
|----------|--------|
| `ANOMALYMATRIX_API_URL` | Backend für Auto-Trigger |
| `OPCUA_API_KEY` | API-Key (Default `amx-key-operator`) |
| `OPCUA_PLC_STOP_ON_RED` | `true` → `StopLineRequest` bei rot |
| `OPCUA_SERVER_ENDPOINT` | OPC-UA Endpoint-URL |

Backend: `GET /api/v1/contracts/opcua` liefert dasselbe NodeSet.

## Docker Compose
Service `opcua-gateway` — Build-Kontext Repo-Root, Ports `8092` + `4840`.
