# scripts

Automation, DB-Migrationen und Installer für AnomalyMatrix.

## Autonome Linux-Installation

**Empfohlenes OS: Ubuntu Server 24.04 LTS**

```bash
# Frisches System
curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
  | sudo bash -s -- --host <SERVER-IP>

# Aus dem Repo
sudo ./scripts/install.sh --mode prod --host <SERVER-IP>
```

Details: `docs/INSTALLATION.md`

## Verzeichnisse

### `scripts/db/`
Postgres-Migrationen (Docker-Init):

| Datei | Inhalt |
|-------|--------|
| `001_init.sql` | Inspection-Ergebnis-Tabelle + Indizes |
| `002_payload_jsonb.sql` | JSONB-Payload-Spalte |
| `003_core_schema.sql` | roles, users, recipes, model_registry, audit, feedback |
| `004_auth_sessions.sql` | password_hash + sessions |
| `005_perf_indexes.sql` | Composite-Index recipe/created |

### Installer
- `install.sh` — Bare-OS → Docker → Production-Stack (Secrets, Firewall, systemd)
- `build_installer.sh` — erzeugt `dist/AnomalyMatrix-installer*.run`
- `publish_github_release.sh` — Tag + GitHub Release inkl. Installer-Assets (`--draft` / `--dry-run`)

### Backup
- `backup/backup.sh` / `backup/restore.sh`
