# Phase 2 Vertical MVP Flow (2026-03-03)

> **Implementierungsstand v0.6.0:** Flow aktiv; Persistenz Postgres oder JSONL; HMI mit Feedback auf Inspection Detail.

## End-to-end path
1. `POST /api/v1/edge/capture`
   - generates synthetic frame + metadata
2. `POST /api/v1/ai/infer`
   - computes deterministic anomaly score + heatmap placeholder URI
3. `POST /api/v1/orchestrate/run-inspection`
   - capture -> infer -> persist minimal result -> response envelope
4. `GET /api/v1/results/latest`
   - retrieves recent persisted results

## Persistence
- Postgres wenn `DATABASE_URL` gesetzt (Docker Compose)
- JSONL-Fallback: `backend/data/inspection_results.jsonl`
- Thread-safe append via lock in repository

## Envelope
All responses follow v1 envelope (`ok`, `data/error`, `meta.requestId`, `meta.timestamp`).
