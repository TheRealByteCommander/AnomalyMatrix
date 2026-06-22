# AnomalyMatrix – Implementation Plan v0.1

## 1) Scope (MVP)
- Eine Prüfstation, ein Bauteiltyp, eine Kamera
- Anomalieerkennung (unüberwacht), Anomalie-Score + Heatmap
- HMI Dashboard + Detailansicht + Feedback (Bestätigen/Korrigieren)
- OPC-UA Kernknoten (Status, Ergebnis, Trigger, Rezeptur)
- Trendanalyse (Basis): gleitender Mittelwert + Warnstufen

## 2) System-Module
1. **edge-acquisition**: Kamera/Beleuchtung, Trigger, Vorverarbeitung
2. **ai-core**: Inferenz + Continual Learning Scheduler
3. **opcua-gateway**: OPC-UA Server + Node Mapping
4. **hmi-web**: React Dashboard (Dark/Tesla-style)
5. **data-layer**: PostgreSQL + InfluxDB + Objektstorage

## 3) Architektur-Entscheidungen (initial)
- Backend: FastAPI + Python 3.12
- KI: PyTorch + OpenCV
- Kommunikation intern: REST + WebSocket
- Deployment: Docker Compose (später K8s optional)

## 4) Delivery Phasen
- **P0 (1-2 Wochen):** Repo-Struktur, API-Verträge, Basis-Infra
- **P1 (3-4 Wochen):** PoC Inferenz + Dashboard live view
- **P2 (4-6 Wochen):** Feedback-Loop + Auto-Retraining + Validierung
- **P3 (3-4 Wochen):** OPC-UA produktionsnah + Trendwarnungen
- **P4 (v0.2.0 Milestone, 2-4 Wochen):** Produktionshärtung mit realer Kamera-/Inferenz-Integration, erweiterte Persistenzabfragen, Operator-Runbook v2, Security/Observability-Finalisierung

## 4.1 Deployment Baseline
- **Aktueller Code-Stand:** `v0.6.0` auf `master`
- **Installer-Baseline:** `v0.1.0` — `dist/AnomalyMatrix-installer-v0.1.0.run`
- **GitHub:** https://github.com/TheRealByteCommander/AnomalyMatrix
- **Erreicht in v0.6.0:** RBAC, Feedback, Core-Schema, PatchCore-MVP, asyncua OPC-UA, Observability
- **Nächster Zielrelease:** `v0.7.0` — E2E-Gates, echtes Modell-Training, JWT-Auth, OPC-UA Sign/Encrypt

## 5) Quality Gates
- Unit + integration tests grün
- Latenzbudget (Inferenz) dokumentiert
- Security-Review (TLS, RBAC, Audit)
- Release Readiness + Deployment Plan verpflichtend

## 6) Offene Entscheidungen
- Exakte Kamera-/Beleuchtungs-Hardware
- Zielzykluszeit pro Use-Case
- Fehlerklassentaxonomie (domänenspezifisch)
- Feedback-Frequenz und Retraining-Policy
