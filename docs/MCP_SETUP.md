# MCP Team-Setup (Cursor & Agenten)

Stand: **v1.2.0** · Projektweite MCP-Server für **eigenes Repo** und **Library-Docs**

| Datei | Zweck |
|-------|--------|
| [`.mcp.json`](../.mcp.json) | Universal (Claude Code, OpenHands, …) |
| [`.cursor/mcp.json`](../.cursor/mcp.json) | Cursor (Projekt-Scope) |

---

## Übersicht

| Server | Zweck | API-Key |
|--------|--------|---------|
| **codebase-memory-mcp** | Knowledge Graph **dieses Repos** (Symbole, Calls, Architektur) | Nein |
| **Context7** | Aktuelle **Library-Dokumentation** (FastAPI, React, asyncua, …) | Optional (höhere Limits) |

**Kombination:** Context7 für externe Frameworks · codebase-memory für AnomalyMatrix-intern.

---

## 1) codebase-memory-mcp

### Installation (einmal pro Rechner)

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash

# Windows (PowerShell)
Invoke-WebRequest -Uri https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.ps1 -OutFile install.ps1
.\install.ps1
```

Alternativ: `npm install -g codebase-memory-mcp` · [GitHub](https://github.com/DeusData/codebase-memory-mcp)

Der MCP-Eintrag erwartet `codebase-memory-mcp` auf dem **PATH**.

### Projekt indexieren

Nach Cursor-Neustart im Chat: **„Index this project“** — oder per CLI:

```bash
codebase-memory-mcp cli index_repository --repo-path . --name AnomalyMatrix
```

Optional mit Team-Artefakt:

```bash
codebase-memory-mcp cli index_repository --repo-path . --name AnomalyMatrix --persistence true
```

Lokaler Cache: `.codebase-memory/` (standardmäßig in `.gitignore`).

### Typische Tools

`index_repository`, `search_graph`, `query_graph`, `trace_path`, `get_architecture`, `search_code`, `detect_changes`

---

## 2) Context7 (Upstash)

[Aktuelle Library-Docs](https://github.com/upstash/context7) für Prompts — reduziert veraltete APIs und Halluzinationen bei FastAPI, Vite, Docker, OPC UA usw.

### Bereits im Repo konfiguriert

Remote-MCP (kein lokales `npx` nötig):

```json
"context7": {
  "url": "https://mcp.context7.com/mcp"
}
```

**Cursor neu starten**, dann sollte `context7` mit Tools `resolve-library-id` und `query-docs` erscheinen.

### Optional: API-Key (empfohlen)

Kostenloser Key: [context7.com/dashboard](https://context7.com/dashboard)

In **Cursor** entweder global in `~/.cursor/mcp.json` oder projektweise in `.cursor/mcp.json` ergänzen:

```json
"context7": {
  "url": "https://mcp.context7.com/mcp",
  "headers": {
    "CONTEXT7_API_KEY": "ihr-api-key"
  }
}
```

> **Hinweis:** API-Keys **nicht** ins Git committen. Jeder Entwickler trägt den Key lokal ein oder nutzt den Free-Tier ohne Header.

Alternativ One-Click-Setup: `npx ctx7 setup --cursor` (OAuth + Key + Skill).

### Nutzung in Prompts

```text
Wie konfiguriere ich FastAPI lifespan? use context7
```

Mit bekannter Library-ID (schneller):

```text
OPC UA asyncua Server-Beispiel. use library /library-id from context7
```

### Empfohlene Cursor-Regel (optional)

```text
Nutze Context7 für Library-/API-Dokumentation und Setup-Schritte.
Nutze codebase-memory-mcp für Fragen zum AnomalyMatrix-Repo selbst.
```

---

## Aktivierung (Checkliste)

1. `codebase-memory-mcp` installieren (siehe oben)
2. Optional: Context7 API-Key in lokaler MCP-Config
3. **Cursor / Agent neu starten**
4. MCP-Liste prüfen: `codebase-memory-mcp` (~15 Tools) + `context7` (2 Tools)
5. „Index this project“ für AnomalyMatrix-Graph

---

## Hinweise

- **Cloud Agents:** Projekt-MCP wird nicht in jeder Cloud-Umgebung geladen — lokal in Cursor Desktop zuverlässiger.
- Nach größeren Refactors: Re-Index (`codebase-memory-mcp`)
- Projekt-`.cursor/mcp.json` ergänzt globale Einträge in `~/.cursor/mcp.json`, ersetzt sie nicht vollständig.
