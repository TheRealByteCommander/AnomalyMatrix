# Ops Runbook: Licensing

Stand: **industrielles Offline-Grant (Produkt 2)** · Server: [software-licensing-concept](https://github.com/TheRealByteCommander/software-licensing-concept)

Industrie-PCs sind **nie online**. Status, Import und Geräte-ID reichen. Stripe/Checkout ist für Produkt 2 deaktiviert (**410**).

## Status

```bash
# Login first (session or Bearer)
TOKEN=$(curl -fsS -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"admin-1","password":"<ADMIN_PW>"}' | jq -r '.data.access_token')

curl -fsS http://127.0.0.1:8080/api/v1/license/status \
  -H "Authorization: Bearer $TOKEN"
```

Erwartete Felder: `active`, `tier`, `features`, `device_id`, `license_key`, `offline=true`, `mode=offline`.

Die `device_id` an den Vendor geben (USB/E-Mail).

## Grant importieren (HMI oder API)

Voraussetzung:

```bash
LICENSE_PRODUCT_ID=2
LICENSE_OFFLINE_ONLY=true
LICENSE_ENFORCE=true
```

HMI: **Einstellungen → Lizenz** → `.lic.json` importieren und optional Lizenznummer eintragen.

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/license/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  --data-binary @/media/usb/AMXB-xxxx.lic.json
```

Nur Nummer, wenn die Datei schon auf dem Gerät liegt:

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/license/import \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"license_key":"XXXX-XXXX-XXXX-XXXX"}'
```

## Activate (Local Bootstrap — nur CI/Dev)

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

Löscht das lokale Grant; es gibt keinen Online-Deactivate.

## ENV (Auszug)

| Variable | Zweck |
|----------|--------|
| `LICENSE_PRODUCT_ID` | Integer, Default 2 |
| `LICENSE_OFFLINE_ONLY` | Default true für Produkt 2 |
| `LICENSE_ENFORCE` | Feature-Gates strikt |
| `LICENSE_ADMIN_TOKEN` | Dual-Control Activate/Deactivate |
| `LICENSE_DEVICE_ID` | Override Fingerprint |
| `LICENSE_GRANT_FILE` | Persistenz `.lic.json` |
| `LICENSE_ALLOW_LOCAL_KEYS` | Notfall `AMX-*` |

## Troubleshooting

| Symptom | Ursache / Aktion |
|---------|------------------|
| **402** auf Inspektion | `LICENSE_ENFORCE=true`, kein gültiger Grant → Datei importieren |
| **402** auf Import | falsche `deviceId`, andere `productId`, ungültige Signatur, abgelaufen |
| **410** auf `/license/checkout` | erwartet — kein Stripe in der Industrie-HMI |
| **403** | Fehlende `license.admin` oder falscher `X-License-Admin-Token` (Activate/Deactivate) |
| **401** | Nicht eingeloggt |
| `offline: true` aber `active: false` | Grant fehlt oder passt nicht zu diesem PC — Geräte-ID prüfen |
