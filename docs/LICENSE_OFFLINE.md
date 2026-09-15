# Offline-Lizenz (Industrie-PC)

AnomalyMatrix (Produkt-ID **2**) läuft **ohne Internetzugang**. Kunden kaufen **nie** in der HMI. Stripe/Checkout ist deaktiviert.

## Ablauf

1. Am Industrie-PC: **Einstellungen → Lizenz** → **Geräte-ID kopieren** und an den Vendor senden.
2. Vendor legt in licadmin eine `feature_based` / `node_locked` Lizenz mit dieser Device-ID an und exportiert `*.lic.json`.
3. Kunde importiert die Datei (USB) und/oder trägt die Lizenznummer ein.
4. Features kommen aus dem signierten Grant. Upgrade = andere Datei / andere Nummer importieren.

Die HMI ruft **kein** `api.activate` / `api.validate` gegen licadmin auf, sobald ein Offline-Grant liegt.

## Geräte-ID

SHA-256-Hex von `{hostname}-{arch}-{os}-{/etc/machine-id}` (sonst MAC via `uuid.getnode()`). Override: `LICENSE_DEVICE_ID` (fertige 64-Hex-ID, wird nicht erneut gehasht).

Demo (nicht produktiv): Rohstring `anomalymatrix-x86_64-Linux-example-machine-id-beta` → `4a0cb3fce728d2f463bf21cb0445eef2c157f79330767711a1ac61cfca967151`.

## Dateiformat `.lic.json`

`format` muss `licenseGrant/v1` sein. Das JWT (`token`) ist RS256-signiert. AnomalyMatrix prüft mit dem **eingebetteten** Public Key (nicht mit `publicKey` aus der Datei).

Claims: `grant=licenseGrant`, `licenseKey`, `productId` (2), `deviceId`, `features`, `offline=true`, `offlineGraceDays`, `expiresAt`, `iat`.

## API

| Methode | Pfad | Zweck |
|---------|------|--------|
| `GET` | `/api/v1/license/status` | `device_id`, `license_key`, `features`, `offline=true` |
| `POST` | `/api/v1/license/import` | Grant-JSON importieren oder Nummer gegen vorhandene Datei |

Beispiel Import:

```bash
curl -fsS -X POST http://127.0.0.1:8080/api/v1/license/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @AMXB-OFFL-DEMO-0001.lic.json
```

## ENV

| Variable | Default | Bedeutung |
|----------|---------|-----------|
| `LICENSE_PRODUCT_ID` | `2` | AnomalyMatrix |
| `LICENSE_OFFLINE_ONLY` | `true` für Produkt 2 | Kein Licadmin-Activate/Validate, kein Stripe |
| `LICENSE_DEVICE_ID` | Auto | Fingerprint-Override |
| `LICENSE_GRANT_FILE` | `backend/data/license_grant.lic.json` | Persistenz des Grants (Mode 0600) |
| `LICENSE_ENFORCE` | Prod `true` | Feature-Gates |

Vendor-Dokumentation: licadmin `docs/ANOMALYMATRIX_OFFLINE.md` (software-licensing-concept).
