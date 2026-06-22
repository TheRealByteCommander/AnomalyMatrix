# Shared Contracts

Versioned schemas used across services. **Stand API v0.6.0.**

- `api_envelope_v1.json` — Response-Envelope (`ok`, `data`, `meta`)
- `events_v1/*.json` — Domain Events (`InspectionCompleted`, `FeedbackSubmitted`, …)
- `opcua_nodeset_mapping_v1.json` — OPC-UA Node-IDs für Gateway
- `inspection_result_v1.json` — Inspection-Ergebnis-DTO

Events **emittiert** in v0.6.0: `InspectionCompleted`, `FeedbackSubmitted`.

**OPC UA v1.1.0:** PLC trigger (`ExternalTrigger`, `StartInspection`), Stop/Reject outputs on red — siehe `opcua-gateway/README.md` und `GET /api/v1/contracts/opcua`.
