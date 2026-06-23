# AnomalyMatrix — Release Readiness Checklist

Stand: **v0.7.0** (2026-06)

## Build & Tests

| Check | Status | Nachweis |
|-------|--------|----------|
| Backend `compileall` | ✅ | CI Job `backend-lint-test` |
| pytest (stub/opencv/patchcore) | ✅ | CI Provider-Matrix |
| E2E Vertical Flow | ✅ | `backend/tests/test_e2e_vertical_flow.py` |
| Frontend production build | ✅ | CI Job `frontend-smoke` |

## Security (MVP)

| Check | Status | Hinweis |
|-------|--------|---------|
| RBAC auf mutierenden Endpunkten | ✅ | Header `X-AMX-Role` / API-Key |
| License enforcement | ✅ | Feature-Gates |
| JWT/Session-Auth | ⏳ | Folgerelease v0.8+ |
| OPC-UA Sign/Encrypt | ⏳ | Folgerelease |

## Observability

| Check | Status |
|-------|--------|
| Domain Events (`InspectionCompleted`, `FeedbackSubmitted`, `TrendWarningRaised`) | ✅ |
| Optional Influx/MinIO | ✅ (env-gesteuert) |

## Dokumentation

| Artefakt | Status |
|----------|--------|
| `README.md` | ✅ |
| `docs/DEPLOYMENT_PLAN.md` | ✅ |
| `docs/RELEASE_NOTES_v0.7.0.md` | ✅ |
| `docs/BUILD_READY_SPEC_V1.md` | ✅ (Fortschritt markiert) |

## Bekannte Grenzen vor Produktion

- Inferenz: PatchCore-MVP-Proxy, kein echtes Training
- Kamera: synthetischer Edge-Stub
- Installer-Artefakt: weiterhin v0.1.0-Baseline — Docker/Git empfohlen

## Freigabe-Empfehlung

**Dev / Pilot / Demo:** freigegeben  
**Unbeaufsichtigte Produktionslinie:** erst nach JWT, OPC-UA TLS und echtem Modell-Training
