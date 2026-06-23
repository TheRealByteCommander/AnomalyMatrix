# AnomalyMatrix — Release Readiness Checklist

Stand: **v0.8.0** (2026-06)

## Build & Tests

| Check | Status | Nachweis |
|-------|--------|----------|
| Backend `compileall` | ✅ | CI |
| pytest (41+ Tests) | ✅ | Provider-Matrix, E2E, Auth, Training, Perf |
| Performance < 500 ms | ✅ | `test_performance_gate.py` |
| Frontend production build | ✅ | CI `frontend-smoke` |
| Playwright HMI E2E | ✅ | CI `frontend-e2e` |

## Security

| Check | Status |
|-------|--------|
| RBAC + API-Key | ✅ |
| JWT + Session Cookie | ✅ v0.8 |
| OPC-UA Sign/Encrypt | ✅ v0.8 (self-signed, env-gated) |
| `JWT_SECRET` in Produktion | ⚠️ Pflicht |

## Produktfeatures v0.8

| Feature | Status |
|---------|--------|
| PatchCore Memory-Bank Training | ✅ MVP |
| Model Promotion + `ModelRetrained` | ✅ |
| OpenCV Kamera (Webcam/Datei) | ✅ |
| Installer v0.8.0 | ✅ |

## Freigabe-Empfehlung

**Dev / Pilot / Demo:** freigegeben  
**Produktion:** `RBAC_ENFORCE=true`, `JWT_SECRET` rotieren, OPC-UA-Zertifikate von PKI, echte Trainingsdaten statt Synthetic-Seed
