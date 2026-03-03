# AnomalyMatrix

Selbstlernende Anomalie-Erkennungssoftware für industrielle Qualitätskontrolle (Klebenähte, Präzisionsbauteile, Lackoberflächen).

## Projektstatus
- Repository initialisiert
- Konzept-Dokument importiert
- Umsetzungsplan (v0.1) erstellt

## Ziele
- Unüberwachte Anomalieerkennung auf Gut-Teilen
- Continual-Learning Feedback-Loop (Human-in-the-Loop)
- OPC-UA Integration (Machine Vision Companion Spec)
- Tesla-inspiriertes, operator-first HMI
- Trendanalyse & Frühwarnungen für Prozessdrift

## Dokumente
- [`docs/KONZEPT_ORIGINAL_2026-02-24.md`](docs/KONZEPT_ORIGINAL_2026-02-24.md)
- [`docs/IMPLEMENTATION_PLAN_V0.1.md`](docs/IMPLEMENTATION_PLAN_V0.1.md)

## Nächste Schritte
1. Zielarchitektur als Monorepo-Scaffold erzeugen (`backend`, `frontend`, `edge-acquisition`, `opcua-gateway`).
2. MVP-Scope finalisieren (Phase 1/2).
3. Datenmodell + API-Verträge fixieren.
4. PoC-Pipeline für Bildakquise -> KI-Inferenz -> HMI aufsetzen.

## Hinweise
Dieses Repo folgt dem Byte-Commander-Standard: Abschluss gilt erst nach Merge in Ziel-Branch mit grünem Test-/Review-Gate.

## Frontend MVP Scaffold (UX/UI)

Path: `frontend/`

Pages (clickable wireframe):
- Dashboard
- Inspection Detail
- Trends
- Configuration

Run locally:
```bash
cd frontend
npm install
npm run dev
```

Build check:
```bash
npm run build
```
