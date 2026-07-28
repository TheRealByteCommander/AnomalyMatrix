# License Integration — Byte Commander License Server

Stand: **v1.1.0** · Upstream: [software-licensing-concept](https://github.com/TheRealByteCommander/software-licensing-concept)  
API-Contract: [`contracts/licensing_openapi.v1.yaml`](../contracts/licensing_openapi.v1.yaml) · Guide: Upstream `INTEGRATION_GUIDE.md`

## Modi

| Modus | Wann | Verhalten |
|-------|------|-----------|
| **Server** | `LICENSE_SERVER_URL` + `LICENSE_PRODUCT_ID` (Integer) gesetzt | Activate / Validate / Deactivate gegen License Server (tRPC) |
| **Local** | Server-URL leer | Bootstrap-Keys `AMX-*` für Installer/CI (kein kryptografischer Schutz) |

## Endpoints (AnomalyMatrix API)

| Methode | Pfad | Auth |
|---------|------|------|
| `GET` | `/api/v1/license/status` | Login + `license.read` |
| `POST` | `/api/v1/license/activate` | Login + `license.admin` + `X-License-Admin-Token` |
| `POST` | `/api/v1/license/deactivate` | Login + `license.admin` + `X-License-Admin-Token` |

Body activate: `{"license_key":"XXXX-…"}`

Status enthält u. a. `active`, `tier`, `features`, `grace_active`, `mode` (`server`|`local`).

## License-Server-Calls (SDK)

Vendored Client: `backend/app/licensing_sdk/` (httpx, tRPC/superjson-Wire-Format).

| Aktion | Upstream |
|--------|----------|
| Activate | `POST /api/trpc/api.activate` |
| Validate | `POST /api/trpc/api.validate` |
| Deactivate | `POST /api/trpc/api.deactivate` |

Request-Envelope: `{"json": { … }}` · Response: `result.data.json`.

## ENV

| Variable | Pflicht (Prod+Server) | Default | Bedeutung |
|----------|----------------------|---------|-----------|
| `LICENSE_SERVER_URL` | für Server-Modus | — | Basis-URL, z. B. `https://license.example.com` |
| `LICENSE_PRODUCT_ID` | für Server-Modus | — | **Integer**-Product-ID vom License Admin |
| `LICENSE_ENFORCE` | ja in Prod | `false` | Feature-Gates (`402` ohne aktive Lizenz) |
| `LICENSE_ADMIN_TOKEN` | ja in Prod | — | Dual-Control für Activate/Deactivate |
| `LICENSE_STATE_FILE` | nein | `backend/data/license_state.json` | Persistenz (Token, Features, Grace) |
| `LICENSE_OFFLINE_GRACE_HOURS` | nein | `72` | Offline-/Fehler-Toleranz |
| `LICENSE_VALIDATE_INTERVAL_SEC` | nein | `300` | Periodische Revalidierung |
| `LICENSE_DEVICE_ID` | nein | Auto | Stabiles Device-Binding; Default: Hash aus Hostname + `/etc/machine-id` |
| `LICENSE_ALLOW_LOCAL_KEYS` | nein | `false` | Notfall: `AMX-*` trotz Server-URL |
| `LICENSE_BOOTSTRAP_KEY` | Installer | — | Echter Key beim Install (Env für `install.sh`) |

## Feature-Gating

Bei `LICENSE_ENFORCE=true` und inaktiver Lizenz:

- `inspection.run` → Capture / Infer / Run-Inspection → **402**
- `inspection.read` → Results / Events → **402**

`license.admin` (Activate/Deactivate) ist **nicht** feature-gegated (sonst Deadlock auf frischem System).

Server-Features (String-Liste) werden auf AMX-Flags gemappt (`inspection.run`, `trends_filters`, `advanced_export`, …). Unbekannte Listen bei gültiger Lizenz → Basis-Inspektionsfeatures.

## Offline / Grace

1. Online-Validate bevorzugt.
2. Bei Netzwerkfehler: Offline-JWT-Decode (ohne Signaturverifikation — MVP; Public-Key-Verify = Folgearbeit).
3. Bei Fehler nach zuvor gültigem Token: Grace-Fenster (`LICENSE_OFFLINE_GRACE_HOURS`).
4. `active` ist true für States `active` | `offline` | `grace` (und `expired` solange `graceUntil` in der Zukunft).

## Installer

- **Ohne** `LICENSE_SERVER_URL`: lokaler Key `AMX-INSTALL-…` (wie bisher).
- **Mit** Server-URL: kein Fake-Key — Aktivierung mit echtem Key (`LICENSE_BOOTSTRAP_KEY` oder manuell via API). Siehe `docs/OPS_LICENSE_RUNBOOK.md`.

## Security notes

- Token/State liegen unter `/app/data` (Docker-Volume `api_data`) — backupen.
- `LICENSE_ADMIN_TOKEN` nur serverseitig, nie im Frontend.
- Signaturprüfung des JWT offline und Vault/KMS für Token-Storage = nächste Härtungsstufe.
- 2FA-Activation (`LicenseClientWith2FA`) ist im Upstream-SDK vorhanden, in AMX noch nicht verdrahtet.

## Verwandte Docs

- `docs/OPS_LICENSE_RUNBOOK.md` — curl / Troubleshooting  
- Upstream `docs/ANLEITUNG_SOFTWARENUTZER.md` / `docs/ANLEITUNG_LIZENZADMIN.md`
