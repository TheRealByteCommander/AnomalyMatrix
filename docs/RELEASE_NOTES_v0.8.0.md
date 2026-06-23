# AnomalyMatrix v0.8.0 – Release Notes

**Datum:** 2026-06  
**Branch:** `master`

## Highlights

### PatchCore Training + Model Promotion
- `POST /api/v1/models/train` — Memory-Bank-Training (Embedding-Proxy, `.npz`)
- `POST /api/v1/models/{id}/promote` — Promotion mit Validierungsgate
- Event `ModelRetrained`
- `PatchCoreInferenceProvider` lädt trainierte Memory Bank

### JWT / Session Auth
- `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`
- Bearer JWT + HttpOnly Session-Cookie (`amx_session`)
- Dev-Login: `admin-1` / `changeme` (JSON-Seed)

### OPC-UA Sign/Encrypt
- `OPCUA_SECURITY_ENABLED=true` aktiviert Basic256Sha256 Sign/Encrypt
- Self-signed Zertifikate via `opcua-gateway/security_config.py`
- Contract: `contracts/opcua_security_profile_v1.json`

### Performance Gates
- `test_performance_gate.py` — Inspection & Inferenz < 500 ms (CI)

### Echte Kamera-Integration
- `edge-acquisition/camera_drivers.py` — OpenCV Webcam/Datei oder Synthetic
- Capture liefert `image_b64` an Backend-Inferenz

### Installer v0.8.0
- `VERSION`-Datei + `dist/AnomalyMatrix-installer-v0.8.0.run`
- Post-Install Smoke (`inspections/run`)

### Playwright HMI E2E
- `frontend/e2e/navigation.spec.js`
- CI-Job `frontend-e2e`

## Upgrade von v0.7.0

```bash
git pull origin master
cd backend && py -3 -m pip install -r requirements.txt
cd ../frontend && npm install
```

Migration: `scripts/db/004_auth_sessions.sql`

## Tests

```bash
cd backend && py -3 -m pytest -q
cd frontend && npm run test:e2e
```
