# Phase 3 – Real Path Upgrade (2026-03-03)

## What changed
1. **Pluggable inference providers**
   - `StubInferenceProvider` (fallback)
   - `OpenCvReadyInferenceProvider` (real-path baseline)
   - provider switch by env: `ANOMALYMATRIX_INFERENCE_PROVIDER`

2. **Persistence query endpoints**
   - `GET /api/v1/results/query` (recipe + score range + limit)
   - `GET /api/v1/results/trend-summary`

3. **OPC-UA publish adapter integration**
   - `map_inspection_to_opcua_payload(...)`
   - publish integration from `run-inspection`

4. **DB migration scripts + Postgres persistence**
   - `scripts/db/001_init.sql`, `scripts/db/002_payload_jsonb.sql`
   - API uses Postgres when `DATABASE_URL` is set (Docker Compose), JSONL fallback for local/tests

5. **Edge + OPC-UA gateway services**
   - `edge-acquisition` HTTP capture wired via `EDGE_ACQUISITION_URL`
   - `opcua-gateway` HTTP `/publish` wired via `OPCUA_GATEWAY_URL`
   - `DefectClass` node mapping per `contracts/opcua_nodeset_mapping_v1.json`

## API additions
- `GET /api/v1/contracts/inspection-result`
- `GET /api/v1/results/query`
- `GET /api/v1/results/trend-summary`

## Known gaps (v0.2.0 follow-up)
- Full asyncua OPC-UA server transport (gateway currently stores mapped nodes in-process).
- InfluxDB metrics pipeline and MinIO heatmap object storage (compose services ready).
- PatchCore model training/inference beyond deterministic provider baselines.
- RBAC, audit log, continual-learning feedback loop (BUILD_READY_SPEC scope).
