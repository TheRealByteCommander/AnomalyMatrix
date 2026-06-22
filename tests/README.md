# tests

Top-Level Integration-Test-Workspace (Platzhalter für künftige E2E-Tests).

## Aktuelle Tests
Backend-Unit- und Integrationstests liegen unter **`backend/tests/`**:

```bash
cd backend
py -3 -m pytest -q
```

Abgedeckt (v0.6.0): API-Envelope, Inspection-Flow, License, Observability, RBAC, Feedback, PatchCore-Provider.

## Geplant
- E2E: capture → inference → decision → feedback (Playwright/pytest)
- OPC-UA Integrationstests gegen Port 4840
- Performance-Gates (< 500 ms Ziel)
