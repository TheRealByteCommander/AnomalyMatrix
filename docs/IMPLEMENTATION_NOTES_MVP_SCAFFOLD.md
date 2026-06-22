# MVP Scaffold Implementation Notes

**Letzte Aktualisierung:** 2026-06 — API **v0.6.0**

## Delivered Structure
- `backend/` — FastAPI mit Envelope, RBAC, License, Catalog, Observability
- `frontend/` — React/Vite HMI (4 Seiten, API-angebunden)
- `edge-acquisition/` — HTTP Capture-Service (`service.py`, Port 8091)
- `opcua-gateway/` — HTTP Gateway + asyncua OPC-UA-Server (8092 / 4840)
- `infra/` — Infra-Manifeste (Platzhalter)
- `scripts/` — DB-Migrationen, Installer
- `tests/` — Top-Level Test-Workspace
- `contracts/` — JSON-Schemas (Envelope, Events, OPC-UA Mapping)

## Backend Contract Decisions
- OpenAPI-first via FastAPI, Version **0.6.0**
- Envelope format aligned to `BUILD_READY_SPEC_V1.md`
- `X-Request-Id` propagated and returned
- RBAC via `X-AMX-Api-Key` oder Dev-Header `X-AMX-Role` / `X-AMX-User` (`RBAC_ENFORCE`)

## Domain Event Contracts (v1)
| Event | Status |
|-------|--------|
| `InspectionCompleted` | ✅ `event_bus` + `GET /events/recent` |
| `FeedbackSubmitted` | ✅ bei `POST /feedback` |
| `ModelRetrained` | 🔜 Schema only |
| `TrendWarningRaised` | 🔜 Schema only |

## Compose Baseline
Services: `api`, `postgres`, `influxdb`, `minio`, `edge-acquisition`, `opcua-gateway`

## Engineering slices — Status

| Slice | Status |
|-------|--------|
| Postgres schema (`recipes`, `audit_log`, `model_registry`, users/roles) | ✅ `003_core_schema.sql` + `CoreStore` |
| Influx write pipeline (`inspection_metrics`) | ✅ optional via `INFLUX_URL` |
| MinIO bucket bootstrap / heatmaps | ✅ optional via `MINIO_ENDPOINT` |
| OPC UA gateway (`StartInspection`, `LastResult`) | ✅ HTTP + asyncua MVP |
| Domain events (`InspectionCompleted`, `FeedbackSubmitted`) | ✅ |
| RBAC (Operator, QA-Lead, Process Engineer, Admin) | ✅ MVP |
| Feedback endpoint + HMI form | ✅ |
| PatchCore inference provider (MVP proxy) | ✅ `patchcore` env |
| Echtes PatchCore-Training / JWT / E2E-Gates | 🔜 |

## Phase 2 — Vertical flow
Synthetic capture → inference → persist → HMI Dashboard/Detail/Trends.

## Phase 3 — Real path
Pluggable providers (`stub`, `opencv_ready`, `patchcore`), Postgres/JSONL repository, query/trend APIs, OPC-UA publish.

## Phase 4 — Observability (v0.5)
Influx metrics, MinIO heatmaps, `GET /observability/summary`.

## Tests
`cd backend && py -3 -m pytest -q` — 27 Tests (inkl. RBAC, Feedback, PatchCore, Observability).
