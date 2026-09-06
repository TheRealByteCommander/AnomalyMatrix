# Ops Runbook: Licensing

Stand: **v1.2.0** (+ Endkunden-Billing) · Server: [software-licensing-concept](https://github.com/TheRealByteCommander/software-licensing-concept)

## Status

```bash
# Login first (session or Bearer)
TOKEN=$(curl -fsS -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"admin-1","password":"<ADMIN_PW>"}' | jq -r '.data.access_token')

curl -fsS http://127.0.0.1:8080/api/v1/license/status \
  -H "Authorization: Bearer $TOKEN"
```

Erwartete Felder: `active`, `tier`, `features`, `grace_active`, `mode` (`server`|`local`).

## Activate (License Server)

Voraussetzung in `.env.production`:

```bash
LICENSE_SERVER_URL=https://licadmin.schmitz.ms
LICENSE_PRODUCT_ID=2
LICENSE_ENFORCE=true
LICENSE_ADMIN_TOKEN=<secret>
```

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/license/activate \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-License-Admin-Token: $LICENSE_ADMIN_TOKEN" \
  -d '{"license_key":"XXXX-XXXX-XXXX-XXXX"}'
```

Installer mit Server: `LICENSE_BOOTSTRAP_KEY=XXXX-… sudo ./scripts/install.sh …`

## Endkunden-Kauf in der HMI (ohne licadmin)

Administrator (`license.admin`) auf **Configuration → License & billing**:

1. Pläne laden: `GET /api/v1/license/plans` (proxied `stripe.plans.listPublic`, gefiltert auf `LICENSE_PRODUCT_ID`)
2. Rechnungs-E-Mail + Tarif → `POST /api/v1/license/checkout` → Redirect auf Stripe-URL
3. Success-URL der HMI: `?checkout=success&session_id={CHECKOUT_SESSION_ID}`
4. Backend holt `stripe.getCheckoutResult` und **aktiviert** den `licenseKey` lokal (Server-Modus)
5. Status / Portal / Kündigung: `GET /api/v1/license/billing`, `POST /api/v1/license/billing/portal`, `POST /api/v1/license/billing/cancel`

```bash
curl -fsS http://127.0.0.1:8080/api/v1/license/plans \
  -H "Authorization: Bearer $TOKEN"

curl -fsS -X POST http://127.0.0.1:8080/api/v1/license/checkout \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"billing_plan_id":1,"customer_email":"ops@example.com","success_url":"http://127.0.0.1:5173/?checkout=success&session_id={CHECKOUT_SESSION_ID}","cancel_url":"http://127.0.0.1:5173/?checkout=cancel"}'
```

`LICENSE_ADMIN_TOKEN` wird für diesen Flow **nicht** ans Frontend gegeben. Return-URLs müssen zu `AMX_CORS_ORIGINS` (oder dem Request-Origin) passen.

## Activate (Local Bootstrap — nur ohne Server-URL)

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/license/activate \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-License-Admin-Token: $LICENSE_ADMIN_TOKEN" \
  -d '{"license_key":"AMX-INSTALL-demo-key-01"}'
```

## Deactivate

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/license/deactivate \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-License-Admin-Token: $LICENSE_ADMIN_TOKEN"
```

## ENV (Auszug)

| Variable | Zweck |
|----------|--------|
| `LICENSE_SERVER_URL` | License-Server Basis-URL |
| `LICENSE_PRODUCT_ID` | Integer Product-ID |
| `LICENSE_ENFORCE` | Feature-Gates strikt |
| `LICENSE_ADMIN_TOKEN` | Admin-Header |
| `LICENSE_OFFLINE_GRACE_HOURS` | Offline-Toleranz |
| `LICENSE_VALIDATE_INTERVAL_SEC` | Hintergrund-Validierung |
| `LICENSE_ALLOW_LOCAL_KEYS` | Notfall `AMX-*` trotz Server |

## Troubleshooting

| Symptom | Ursache / Aktion |
|---------|------------------|
| **402** auf Inspektion | `LICENSE_ENFORCE=true`, Lizenz nicht `active`/`grace`/`offline` → activate |
| **402** auf activate | Server lehnte Key ab / Netzwerk — `last_error` im Status (non-prod) |
| **403** | Falscher `X-License-Admin-Token` oder fehlende `license.admin` |
| **401** | Nicht eingeloggt |
| `mode: local` wider Erwarten | `LICENSE_SERVER_URL` oder `LICENSE_PRODUCT_ID` (muss Integer sein) fehlt im Container |
| Offline nach Netzausfall | Grace-Fenster; Token unter Volume `api_data` prüfen |
