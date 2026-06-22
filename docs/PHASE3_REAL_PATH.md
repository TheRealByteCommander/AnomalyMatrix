# Phase 3 – Real Path Upgrade

**Stand:** v0.6.0 (2026-06)

## What changed
1. **Pluggable inference providers**
   - `StubInferenceProvider` (fallback)
   - `OpenCvReadyInferenceProvider` (real-path baseline)
   - `PatchCoreInferenceProvider` (MVP: OpenCV-Textur + Hash-Proxy)
   - Env: `ANOMALYMATRIX_INFERENCE_PROVIDER=stub|opencv_ready|patchcore`

2. **Persistence query endpoints**
   - `GET /api/v1/results/query` (recipe + score range + limit)
   - `GET /api/v1/results/trend-summary`

3. **OPC-UA publish adapter integration**
   - `map_inspection_to_opcua_payload(...)`
   - publish integration from `run-inspection`
   - Gateway: asyncua-Server auf Port **4840** (`opcua_server.py`)

4. **DB migration scripts + Postgres persistence**
   - `scripts/db/001_init.sql`, `002_payload_jsonb.sql`, `003_core_schema.sql`
   - API uses Postgres when `DATABASE_URL` is set; JSONL fallback for local/tests
   - `CoreStore` für recipes, models, audit, feedback

5. **Edge + OPC-UA gateway services**
   - `edge-acquisition` HTTP capture via `EDGE_ACQUISITION_URL`
   - `opcua-gateway` HTTP `/publish` via `OPCUA_GATEWAY_URL`
   - `DefectClass` node mapping per `contracts/opcua_nodeset_mapping_v1.json`

6. **RBAC + Feedback (v0.6)**
   - Rollen: operator, qa_lead, process_engineer, admin
   - `POST/GET /api/v1/feedback`, Audit-Log, `FeedbackSubmitted` event

7. **Observability (v0.5)**
   - Influx metrics, MinIO heatmaps (optional)
   - `GET /api/v1/observability/summary`, `GET /api/v1/events/recent`

## API additions (kumulativ)
- `GET /api/v1/contracts/inspection-result`
- `GET /api/v1/results/query`, `GET /api/v1/results/trend-summary`
- `GET /api/v1/recipes`, `GET /api/v1/models`
- `POST /api/v1/feedback`, `GET /api/v1/feedback`
- `GET /api/v1/audit/recent`
- `GET /api/v1/observability/summary`
- `GET /api/v1/events/recent`

## Known gaps (Folgerelease)
- Echtes PatchCore-Modell-Training und Embedding-Memory-Bank
- OPC-UA Sign/Encrypt + Zertifikats-Auth (Produktionsprofil)
- JWT/Session-Auth statt Header/API-Key MVP
- WebSocket Live-View im HMI
- E2E/Performance/Security-Gates vollständig automatisiert
- Auto-Retraining (`ModelRetrained`) und Trend-Warn-Engine (`TrendWarningRaised`)
