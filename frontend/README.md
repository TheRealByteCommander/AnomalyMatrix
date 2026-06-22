# frontend

React/Vite HMI für AnomalyMatrix (**v0.6.0**).

## Seiten
| Seite | Funktion |
|-------|----------|
| Dashboard | Inspection auslösen, KPIs, letzte Ergebnisse |
| Inspection Detail | Score, Heatmap-Platzhalter, **QA-Feedback** |
| Trends | Trend-Summary aus API |
| Configuration | License, Recipes/Models aus API |
| **Hilfe & FAQ** | Durchsuchbare Wissensdatenbank, FAQ, Glossar |

## Sprachen
- **Deutsch** und **English** — Umschalter oben rechts auf dem Hauptbildschirm
- Auswahl wird in `localStorage` (`amx-locale`) gespeichert
- Hilfe-Artikel in beiden Sprachen (`help/helpContent.de.js`, `help/helpContent.en.js`)
- Tab **Hilfe & FAQ** — Bedienung, **Anwendung & Einsatz**, Arbeitsabläufe, Glossar
- Schwebender **?**-Button — Schnellsuche
- **F1** — Hilfe-Drawer
- Kontext-Link auf jedem Bildschirm
- Keine Installations- oder IT-Dokumentation in der Hilfe

## Voraussetzungen
- **Node.js 18+** (Vite 8)
- Backend auf Port **8080** (`py -3 -m uvicorn app.main:app --reload --port 8080`)

## Entwicklung
```bash
npm install
npm run dev
```

URL: [http://localhost:5173](http://localhost:5173)

## Build
```bash
npm run build
npm run preview   # lokale Vorschau des Builds
npm run smoke     # = build (CI-Check)
```

## Umgebungsvariablen (optional, `frontend/.env`)

```env
VITE_API_BASE=http://127.0.0.1:8080/api/v1
VITE_AMX_ROLE=operator
VITE_AMX_USER=hmi-operator
VITE_AMX_FEEDBACK_ROLE=qa_lead
```

## API-Mapping
`src/services.js` — `mapApiInspection()` mappt Backend-DTO auf HMI-View-Model.
