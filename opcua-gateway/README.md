# opcua-gateway

OPC-UA-Gateway für AnomalyMatrix (**v0.3.0**).

## Funktion
- HTTP-API für Publish aus der Backend-Inspection-Pipeline
- **asyncua** OPC-UA-Server im Hintergrund (Port **4840**)
- Node-Mapping gemäß `contracts/opcua_nodeset_mapping_v1.json`

## Ports
| Port | Protokoll |
|------|-----------|
| 8092 | HTTP (FastAPI) |
| 4840 | OPC-UA (`opc.tcp://…/anomalymatrix/server/`) |

## Lokal starten
```bash
pip install -r requirements.txt
uvicorn gateway_service:app --host 0.0.0.0 --port 8092
```

## Endpoints
- `GET /health` — Service-Status
- `POST /publish` — Inspection-Payload → OPC-UA-Variablen
- `GET /nodes` — letzte geschriebene Nodes (Debug)

## Umgebungsvariablen
| Variable | Default |
|----------|---------|
| `OPCUA_SERVER_ENABLED` | `true` |
| `OPCUA_SERVER_ENDPOINT` | `opc.tcp://0.0.0.0:4840/anomalymatrix/server/` |

## Docker Compose
Service `opcua-gateway` — Ports `8092:8092`, `4840:4840`.

Backend `.env`: `OPCUA_GATEWAY_URL=http://opcua-gateway:8092` (Compose) bzw. `http://127.0.0.1:8092` (lokal).
