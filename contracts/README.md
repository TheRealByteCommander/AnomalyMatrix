# Shared Contracts

Versioned schemas used across services. **Stand API v1.2.0 + AI-Vision EOL 1.0.**

- `api_envelope_v1.json` — Response-Envelope (`ok`, `data`, `meta`)
- `events_v1/*.json` — Domain Events (`InspectionCompleted`, `FeedbackSubmitted`, …)
- `opcua_nodeset_mapping_v1.json` — OPC-UA Node-IDs für Gateway (inkl. EPC)
- `inspection_result_v1.json` — Inspection-Ergebnis-DTO
- `image_asset_v1.json` — ImageAsset (Object-Key, Format, Legal-Hold)
- `capture_set_v1.json` — CaptureSet (Bildsatz je EPC)
- `epc_binding_v1.json` — EpcBinding
- `station_vision_profile_v1.json` — StationVisionProfile
- `retention_policy_v1.json` — RetentionPolicy

Events **emittiert**: `InspectionCompleted`, `FeedbackSubmitted`.

**OPC UA v1.2.0:** PLC trigger (`ExternalTrigger`, `StartInspection`), Stop/Reject outputs on red, `Request.Epc` / `LastResult.Epc` — siehe `opcua-gateway/README.md` und `GET /api/v1/contracts/opcua`.

EOL-Schemas: `GET /api/v1/contracts/eol`.
