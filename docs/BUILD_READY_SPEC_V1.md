# AnomalyMatrix – Build Ready Spec v1

## 1. API & Contract Standards
- REST API via FastAPI, OpenAPI-first.
- Standard response envelope:
  - success: `{ ok: true, data, meta }`
  - error: `{ ok: false, error: { code, message, details, retryable }, meta: { requestId, timestamp } }`
- Request correlation mandatory (`X-Request-Id`).
- Internal domain events (JSON schema, versioned):
  - `InspectionCompleted`
  - `FeedbackSubmitted`
  - `ModelRetrained`
  - `TrendWarningRaised`

## 2. OPC UA Contract (Machine Vision-aligned)
- Core nodes/groups (versioned NodeSet mapping):
  - System State/Health
  - Active Recipe
  - StartInspection (method)
  - LastResult (PassFail, AnomalyScore, DefectClass)
  - Trend Warning flags
- Recipe- and signal-mapping configurable in HMI with validation.
- Production profile: Sign/Encrypt + certificate auth mandatory.

## 3. Data Model (Source of Truth)
### PostgreSQL
- `recipes`, `users`, `roles`, `audit_log`, `feedback_events`, `model_registry`.
- Required versioning fields: `recipe_version`, `model_version`, `dataset_version`.

### InfluxDB
- `inspection_metrics` (score, latency, confidence)
- `process_trends` (rolling mean/stddev, drift score)
- `system_health_metrics`

### Object Storage (MinIO/S3)
- `raw_images/`
- `heatmaps/`
- `training_artifacts/`
- `model_binaries/`

## 4. AI/MLOps Policy
- Initial primary model: PatchCore (MVP default).
- Alternate profile: AE/VAE stack for constrained hardware.
- Continual learning guardrails:
  1) minimum validated feedback batch threshold
  2) shadow validation on holdout set
  3) promote only on non-regression + KPI improvement
  4) rollback capability < 60s
- Model promotion requires signed validation report.

## 5. Performance & Hardware Budget
- End-to-end inspection cycle target: **< 500 ms**
  - capture: 10–50 ms
  - preprocessing: 5–20 ms
  - inference: 20–200 ms
  - publish/result: < 10 ms
- Recipe must persist full capture + lighting profile.

## 6. Security Baseline (IEC 62443-oriented)
- RBAC roles:
  - Operator
  - QA-Lead
  - Process Engineer
  - Admin
- Immutable audit requirements:
  - actor, action, before/after, timestamp, reason, approval context
- Secret handling via env/secret store only; no plain-text keys in repo.
- Network zoning and conduit rules documented per deployment.

## 7. Test Strategy (Mandatory Gates)
- Unit tests (logic/validation)
- Integration tests (service boundaries, OPC UA, DB)
- E2E tests (capture -> inference -> decision -> feedback)
- Performance tests under realistic load
- Drift/false-warning resilience tests
- Security regression checks (authn/authz/audit)

## 8. Observability & Ops
- Metrics (minimum):
  - API p95 latency
  - inference p95 latency
  - queue lag
  - OPC UA publish error rate
  - storage write lag
- Structured logs with requestId + correlationId.
- Alerting thresholds for trend warnings, latency breach, component health.

## 9. Deployment & Recovery
- MVP runtime: Docker Compose (modular services).
- Upgrade strategy: rolling service updates with health gates.
- Backup/restore:
  - daily DB snapshots
  - model artifact retention policy
  - periodic restore drill

## 10. Definition of Done (Project Gate)
A release/project increment is only complete when all are true:
1. Tests green (unit/integration/E2E/perf where applicable)
2. Release Readiness Check documented
3. Deployment Plan documented
4. Security checks passed
5. Changes merged to target branch on GitHub

## 11. Immediate Next Execution Steps

### Erledigt (Stand v0.6.0, `master`)
- [x] Repository scaffold (`backend`, `frontend`, `edge-acquisition`, `opcua-gateway`, `infra`, `docs`)
- [x] OpenAPI v1 Envelope + Domain-Event-Schemas
- [x] MVP vertical slice (single recipe / single camera)
- [x] Postgres core schema (`recipes`, `users`, `roles`, `audit_log`, `feedback_events`, `model_registry`)
- [x] RBAC MVP (Operator, QA-Lead, Process Engineer, Admin)
- [x] Feedback-Loop + `FeedbackSubmitted`
- [x] PatchCore inference provider (MVP-Proxy)
- [x] OPC-UA asyncua gateway (Port 4840)
- [x] Observability (Influx/MinIO optional)
- [x] Unit/Integration tests (backend pytest)

### Offen (Folgerelease)
1) CI gates für lint/test/security vollständig automatisieren
2) E2E-Tests (capture → inference → decision → feedback)
3) Echtes PatchCore-Training + Model-Registry-Promotion
4) OPC-UA Sign/Encrypt + Zertifikats-Auth
5) JWT/Session-Auth, WebSocket Live-View
6) Performance-Tests unter Last (< 500 ms Ziel)
