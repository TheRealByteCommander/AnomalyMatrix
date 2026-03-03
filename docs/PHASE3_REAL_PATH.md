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

4. **DB migration scripts**
   - `scripts/db/001_init.sql`
   - `scripts/db/apply_migrations.sh`

## API additions
- `GET /api/v1/contracts/inspection-result`
- `GET /api/v1/results/query`
- `GET /api/v1/results/trend-summary`

## Known gaps
- OPC-UA transport is still a skeleton (payload mapping concrete, network publish stubbed).
- Postgres persistence is prepared via migration scripts but API still stores MVP results in JSONL.
