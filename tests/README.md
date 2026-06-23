# tests

Integration- und E2E-Tests für AnomalyMatrix.

## Backend (pytest)

```bash
cd backend
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r ../opcua-gateway/requirements.txt
py -3 -m pytest -q
```

**Stand v0.8.0 (41+ Tests):** API, E2E Vertical Flow, Auth JWT/Session, Training/Promotion, Performance Gate, OPC-UA Security.

## Frontend (Playwright)

```bash
cd frontend
npm ci --legacy-peer-deps
npx playwright install chromium
npm run test:e2e
```

## CI

- `backend-lint-test` — pytest Provider-Matrix
- `frontend-smoke` — Vite build
- `frontend-e2e` — Playwright Navigation + Dashboard
