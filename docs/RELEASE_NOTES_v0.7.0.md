# AnomalyMatrix v0.7.0 – Release Notes

**Datum:** 2026-06  
**Branch:** `master`

## Highlights

### Trend-Warn-Engine
- Rolling-Analyse der letzten Inspektionen (`trend_engine.py`)
- `GET /results/trend-summary` liefert `trend_warning`, `trend_severity`, `trend_reason`
- Event `TrendWarningRaised` bei neuer Warnstufe (Dedup pro Rezept/Schweregrad)
- OPC-UA `trend_warning`-Node wird bei Inspektion befüllt

### E2E & CI
- Neuer Test: `test_e2e_vertical_flow.py` (capture → infer → run → feedback)
- CI: Frontend `npm run smoke` + pytest mit `patchcore`-Provider

### HMI
- Dashboard: Rezept/Modell/Kamera und Trend-Status aus API
- Trends: Trendwarnung aus API
- Accessibility: Skip-Link, `:focus-visible`-Ringe

### Dokumentation
- `docs/RELEASE_READINESS.md`
- `docs/DEPLOYMENT_PLAN.md`

## API

Version **0.7.0** (`backend/app/main.py`)

## Upgrade von v0.6.0

```bash
git pull origin master
cd backend && py -3 -m pip install -r requirements.txt
cd ../frontend && npm install
```

Keine Schema-Migration erforderlich.

## Bekannte Grenzen (unverändert)

- Echtes PatchCore-Training
- JWT/Session-Auth
- OPC-UA Sign/Encrypt
- Installer v0.1.0-Baseline

## Tests

```bash
cd backend && py -3 -m pytest -q   # 35+ Tests
cd frontend && npm run smoke
```
