# License Integration — Byte Commander License Server

Stand: **industrielles Offline-Grant** (Produkt 2) · Upstream: [software-licensing-concept](https://github.com/TheRealByteCommander/software-licensing-concept)  
API-Contract: [`contracts/licensing_openapi.v1.yaml`](../contracts/licensing_openapi.v1.yaml) · Operator-Notiz: [`LICENSE_OFFLINE.md`](./LICENSE_OFFLINE.md)

## Modi

| Modus | Wann | Verhalten |
|-------|------|-----------|
| **Offline** (Default, Produkt 2) | `LICENSE_OFFLINE_ONLY` nicht `false`, bzw. Produkt-ID 2 | Signierte `.lic.json` lokal per RS256 prüfen. **Kein** `api.activate` / `api.validate`, **kein** Stripe. |
| **Server** | `LICENSE_OFFLINE_ONLY=false` und `LICENSE_SERVER_URL` + Integer-`LICENSE_PRODUCT_ID` | Activate / Validate / Deactivate gegen License Server (tRPC) — nicht für AnomalyMatrix-Industrie-PCs. |
| **Local** | Kein Grant, nicht Prod, `AMX-*` Keys | Bootstrap für Installer/CI (kein kryptografischer Schutz) |

## Endpoints (AnomalyMatrix API)

| Methode | Pfad | Auth |
|---------|------|------|
| `GET` | `/api/v1/license/status` | Login + `license.read` |
| `POST` | `/api/v1/license/import` | Login + `license.admin` |
| `POST` | `/api/v1/license/activate` | Login + `license.admin` + `X-License-Admin-Token` |
| `POST` | `/api/v1/license/deactivate` | Login + `license.admin` + `X-License-Admin-Token` |

Stripe/Checkout-Routen (`/license/plans`, `/license/checkout`, `/license/billing`, …) antworten für Produkt 2 mit **410**.

Body import: die `.lic.json` selbst oder `{"grant":{…},"license_key":"optional"}`.

Status enthält u. a. `active`, `tier`, `features`, `device_id`, `license_key`, `offline`, `mode` (`offline`\|`server`\|`local`), `billing_enabled=false`.

**Kein Endkunden-Kauf in der HMI.** Vendor erzeugt den Key in licadmin; der Kunde importiert die Datei unter Einstellungen → Lizenz.

## License-Server-Calls (SDK)

Vendored Client: `backend/app/licensing_sdk/` (httpx, tRPC/superjson-Wire-Format). Offline-Verifier: `licensing_sdk/offline.py` (eingebetteter RS256-Public-Key).

| Aktion | Upstream |
|--------|----------|
| Offline-Grant | lokale RS256-Prüfung, Datei `licenseGrant/v1` |
| Activate | `POST /api/trpc/api.activate` (nicht bei Offline-Grant / Produkt 2) |
| Validate | `POST /api/trpc/api.validate` (nicht bei Offline-Grant / Produkt 2) |
| Deactivate | `POST /api/trpc/api.deactivate` (nicht im Offline-Pfad) |

## ENV

| Variable | Pflicht (Prod) | Default | Bedeutung |
|----------|----------------|---------|-----------|
| `LICENSE_PRODUCT_ID` | ja | `2` | Integer-Product-ID (AnomalyMatrix = **2**) |
| `LICENSE_OFFLINE_ONLY` | nein | `true` für Produkt 2 | Industrieller Offline-Pfad |
| `LICENSE_ENFORCE` | ja in Prod | `false` | Feature-Gates (`402` ohne aktive Lizenz) |
| `LICENSE_ADMIN_TOKEN` | ja in Prod | — | Dual-Control für Activate/Deactivate (nicht für HMI-Import) |
| `LICENSE_STATE_FILE` | nein | `backend/data/license_state.json` | Persistenz (Features, Status) |
| `LICENSE_GRANT_FILE` | nein | `backend/data/license_grant.lic.json` | Signiertes Grant (0600) |
| `LICENSE_OFFLINE_GRACE_HOURS` | nein | `72` | Grace nach Ablauf (`expiresAt`) |
| `LICENSE_VALIDATE_INTERVAL_SEC` | nein | `300` | Periodische Revalidierung (lokal) |
| `LICENSE_DEVICE_ID` | nein | Auto | Fertige SHA-256-Hex-ID; sonst Hash aus Hostname + `/etc/machine-id` |
| `LICENSE_ALLOW_LOCAL_KEYS` | nein | `false` | Notfall: `AMX-*` trotz Offline-Only |
| `LICENSE_SERVER_URL` | nur Nicht-Offline | — | Nicht für Industrie-PCs setzen |
| `LICENSE_BOOTSTRAP_KEY` | Installer | — | Nur CI/`AMX-*`, nicht der Industrie-Pfad |

## Feature-Gating

Bei `LICENSE_ENFORCE=true` und inaktiver Lizenz:

- `inspection.run` → Capture / Infer / Run-Inspection → **402**
- `inspection.read` → Results / Events → **402**

`license.admin` (Import/Activate) ist **nicht** feature-gegated (sonst Deadlock auf frischem System).

Grant-Features (String-Liste) werden case-insensitive auf AMX-Flags gemappt (`basic`, `inspection`/`inspection.run`, `Trends`/`trends_filters`, `Export`/`advanced_export`, …). Gültiger Grant mit `grant_core` schaltet Inspektion/Training frei.

## Offline / Grace

1. Vorhandene `.lic.json` lokal per RS256 prüfen (Public Key in AMX gepinnt).
2. `deviceId` muss zur aktuellen `get_device_id()` passen; `productId` muss 2 (oder `LICENSE_PRODUCT_ID`) sein.
3. Bei Ablauf (`expiresAt` / JWT `exp`): Grace-Fenster.
4. `active` ist true für States `active` | `offline` | `grace`.

## Installer

- Industrie: kein Fake-Key, kein Licadmin-Activate. Geräte-ID in der HMI kopieren, Grant importieren.
- CI/Dev: `AMX-INSTALL-…` bleibt ohne Produktionsumgebung nutzbar.

## Security notes

- Grant/State liegen unter `/app/data` (Docker-Volume `api_data`) mit Dateimodus 0600 — backupen.
- `LICENSE_ADMIN_TOKEN` nur serverseitig, nie im Frontend. HMI-Import braucht Session + `license.admin`.
- Die Datei darf einen `publicKey` enthalten; AMX **ignoriert** ihn und prüft nur den eingebetteten Key.

## Verwandte Docs

- `docs/LICENSE_OFFLINE.md` — Operator/Vendor Kurzablauf
- `docs/OPS_LICENSE_RUNBOOK.md` — curl / Troubleshooting
- Upstream `docs/ANOMALYMATRIX_OFFLINE.md`
