# codebase-memory-mcp — Team-Setup

Stand: **v1.2.0** · MCP-Server für strukturelle Code-Intelligenz (Knowledge Graph)

Das Repo enthält eine **projektweite MCP-Konfiguration**:

| Datei | Zweck |
|-------|--------|
| [`.mcp.json`](../.mcp.json) | Universal (Claude Code, OpenHands, …) |
| [`.cursor/mcp.json`](../.cursor/mcp.json) | Cursor (Projekt-Scope) |

## Voraussetzung: Binary installieren

Der MCP-Eintrag erwartet `codebase-memory-mcp` auf dem **PATH** (einmal pro Entwickler-Rechner):

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash

# Windows (PowerShell)
Invoke-WebRequest -Uri https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.ps1 -OutFile install.ps1
.\install.ps1
```

Alternativ: `npm install -g codebase-memory-mcp` · Details: [GitHub](https://github.com/DeusData/codebase-memory-mcp)

## Cursor / Agent aktivieren

1. Binary installieren (siehe oben)
2. **Cursor neu starten** (MCP-Server werden beim Start geladen)
3. In Cursor: MCP prüfen — `codebase-memory-mcp` sollte mit ~15 Tools erscheinen
4. Im Chat: **„Index this project“** oder Index per CLI:

```bash
codebase-memory-mcp cli index_repository --repo-path . --name AnomalyMatrix
```

## Optional: Team-Artefakt (schnellerer Erst-Index)

Mit Persistenz wird ein komprimierter Graph unter `.codebase-memory/graph.db.zst` erzeugt — Teammitglieder können davon bootstrappen:

```bash
codebase-memory-mcp cli index_repository --repo-path . --name AnomalyMatrix --persistence true
```

Standard: Verzeichnis ist in `.gitignore` (jeder indexiert lokal). Zum Teilen im Repo Artefakt committen und `.codebase-memory/` aus `.gitignore` entfernen.

## Typische MCP-Tools

| Tool | Nutzen |
|------|--------|
| `index_repository` | Projekt indexieren / aktualisieren |
| `search_graph` / `query_graph` | Symbole, Abhängigkeiten, Aufrufketten |
| `trace_path` | Pfad zwischen zwei Symbolen |
| `get_architecture` | Architektur-Überblick |
| `search_code` | Textsuche mit Graph-Kontext |
| `detect_changes` | Index vs. Git-Stand |

## Hinweise

- Nach größeren Refactors: Index erneut ausführen oder „Re-index this project“
- Projekt-Konfiguration überschreibt nicht globale MCP-Einträge in `~/.cursor/mcp.json`
- Kein API-Key, kein Docker — lokaler stdio-MCP-Server
