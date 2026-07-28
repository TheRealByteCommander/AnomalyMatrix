# AnomalyMatrix — Anwendung & Einsatzgebiete

Stand: **v1.2.0** (Produktdokumentation, ergänzt HMI-Hilfe)

## Kurzfassung

**AnomalyMatrix** ist Software für **automatische Anomalieerkennung** in der industriellen Fertigung. Sie vergleicht aktuelle Prüfbilder mit einem Modell „guter“ Teile, liefert einen **Anomalie-Score** und eine **Ampelentscheidung** (grün / gelb / rot), bindet sich an **OPC UA** an die SPS an und bietet ein **Operator-HMI** mit QA-Feedback, Multi-Kamera-Prüfung (1–4 Views) und **Drift pro Kamera**.

## Kernproblem

Klassische Bildverarbeitung verlangt die explizite Definition jedes Fehlers. In flexiblen oder veränderlichen Prozessen (Verschleiß, Materialchargen, Nacharbeit) ist das aufwendig und fehleranfällig. AnomalyMatrix adressiert **unbekannte oder seltene Abweichungen** durch unüberwachtes Lernen auf Gut-Teilen.

## Typische Einsatzgebiete

### 1. Inline-Qualitätskontrolle

- Nach Kleben, Schweißen, Lackieren, Etikettieren, Montage
- 100-%-Prüfung an Engpässen
- SPS gibt Teil frei oder stoppt bei rot

### 2. Automatisierung mit der SPS (OPC UA)

- **Trigger:** `ExternalTrigger`, `StartRequest` oder Methode `StartInspection`
- **Reaktion:** `StopLineRequest`, `RejectPart` bei rot
- **Quittierung:** `AcknowledgeStop` für sichere Wiederanlauf-Logik

### 3. Prozessüberwachung & Drift

- Gleitende Verschlechterung des Scores über Schichten — bei Multi-View **pro Kamera**
- KPIs: Anomaliequote, Zyklus-p95, Trendwarnung
- Frühwarnung für Wartung / Parameterkorrektur

### 4. Qualitätssicherung & Dokumentation

- QA bewertet Ergebnisse (bestätigen / falsch positiv / Nachprüfung)
- Audit-Log und Domain-Events
- Grundlage für Continual Learning (Roadmap)

## Zielgruppen

| Rolle | Nutzen |
|-------|--------|
| Operator | Prüfung starten oder per SPS auslösen, Ampel interpretieren |
| QA Lead | Feedback, Freigabe/Sperre unterstützen |
| Prozessingenieur | Trends, Drift je Kamera, Rezept- und Modellversion |
| Automatisierung | OPC-UA-NodeSet in SPS-Programm einbinden |

## Softwarebestandteile (Überblick)

- **Backend:** Inspektionspipeline, Multi-Kamera, Persistenz, RBAC, Lizenz, Observability
- **Frontend (HMI):** Dashboard, Detail (Multi-View), Trends (Drift je Kamera), Konfiguration, Hilfe (DE/EN)
- **OPC-UA-Gateway:** Server Port 4840, PLC-Signale, Contract v1.2 (Multi-View + Drift)
- **Edge-Acquisition:** Kamera-Discovery, Capture (OpenCV/V4L2 oder synthetic)

## Abgrenzung

- Ersetzt **nicht** werksverbindliche QS-Freigabeprozesse
- Liefert **Hinweise** (Score, Heatmap, DefectClass), keine automatische Root-Cause-Analyse
- Messtechnische Toleranzprüfung nur bei entsprechender Rezept-/Modellkonfiguration

## Weitere Informationen

- HMI: Tab **Hilfe & FAQ** → Kategorie **Anwendung & Einsatz**
- Technik: `docs/MULTI_CAMERA.md`, `docs/BUILD_READY_SPEC_V1.md`, `opcua-gateway/README.md`
- API-Contract: `GET /api/v1/contracts/opcua`

---

# AnomalyMatrix — Application & Use Cases (EN)

## Summary

**AnomalyMatrix** is software for **automated anomaly detection** in manufacturing. It compares inspection images to a model of good parts, returns an **anomaly score** and **traffic-light decision**, integrates with the **PLC via OPC UA**, and provides an **operator HMI** with QA feedback and trends.

## Typical use cases

1. **Inline QC** — 100% inspection after critical process steps  
2. **PLC automation** — triggers, stop/reject on red, acknowledge stop  
3. **Process monitoring** — drift detection via trends and KPIs  
4. **Quality loop** — human feedback for audit and model improvement  

See the in-app **Help & FAQ** tab (category **Application & Use Cases**) for the full bilingual knowledge base.
