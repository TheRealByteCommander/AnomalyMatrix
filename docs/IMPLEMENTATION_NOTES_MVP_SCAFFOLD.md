# MVP Scaffold Implementation Notes (2026-03-03)

## Delivered Structure
- `backend/` FastAPI bootstrap with request correlation and standard envelope.
- `frontend/` placeholder workspace for upcoming UI implementation.
- `edge-acquisition/` reserved for camera/lighting collector service.
- `opcua-gateway/` reserved for OPC UA bridge.
- `infra/` infrastructure manifests placeholder.
- `scripts/` helper scripts placeholder.
- `tests/` global test workspace placeholder.

## Backend Contract Decisions
- OpenAPI-first via FastAPI.
- Envelope format aligned to `BUILD_READY_SPEC_V1.md`:
  - success: `{ ok, data, meta }`
  - error: `{ ok:false, error:{code,message,details,retryable}, meta:{requestId,timestamp} }`
- `X-Request-Id` propagated and returned.

## Domain Event Contracts (v1)
- `InspectionCompleted`
- `FeedbackSubmitted`
- `ModelRetrained`
- `TrendWarningRaised`

## Compose Baseline
Services included:
- `api`
- `postgres`
- `influxdb`
- `minio`

## Next engineering slice
1. Postgres schema migration baseline (`recipes`, `audit_log`, `model_registry`).
2. Influx write pipeline for `inspection_metrics`.
3. MinIO bucket bootstrap and object naming conventions.
4. OPC UA gateway MVP (`StartInspection`, `LastResult`).
