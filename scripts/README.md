# scripts

Automation, DB-Migrationen und Installer für AnomalyMatrix.

## Verzeichnisse

### `scripts/db/`
Postgres-Migrationen (werden bei Docker-Init automatisch ausgeführt):

| Datei | Inhalt |
|-------|--------|
| `001_init.sql` | Inspection-Ergebnis-Tabelle |
| `002_payload_jsonb.sql` | JSONB-Payload-Spalte |
| `003_core_schema.sql` | roles, users, recipes, model_registry, audit_log, feedback_events + Seed |

Manuell anwenden:
```bash
./scripts/db/apply_migrations.sh
```

### Installer
- `build_installer.sh` — erzeugt `dist/AnomalyMatrix-installer*.run`
- `install.sh` — direkte Installation ohne One-File-Wrapper

Siehe `docs/INSTALLATION.md`.
