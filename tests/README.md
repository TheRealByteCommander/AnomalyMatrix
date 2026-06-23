# tests

Integration- und E2E-Tests für AnomalyMatrix.

## Backend (pytest)

```bash
cd backend
py -3 -m pip install -r requirements.txt
py -3 -m pytest -q
```

**Stand v0.7.0:** API-Envelope, Inspection-Flow, License, Observability, RBAC, Feedback, OPC-UA PLC, Trend-Engine, **E2E Vertical Flow** (`test_e2e_vertical_flow.py`).

## CI

GitHub Actions (`.github/workflows/ci.yml`):

- Backend: `compileall` + pytest mit Provider-Matrix (`stub`, `opencv_ready`, `patchcore`)
- Frontend: `npm run smoke` (Vite production build)

## Geplant (Folgerelease)

- Playwright HMI-E2E
- OPC-UA Integrationstests gegen Port 4840 (live asyncua)
- Performance-Gates (< 500 ms Ziel)
