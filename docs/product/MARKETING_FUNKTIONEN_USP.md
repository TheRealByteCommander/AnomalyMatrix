# AnomalyMatrix — Marketing-Handbuch  
## Funktionen, Alleinstellungsmerkmale & Botschaften

**Produkt:** AnomalyMatrix **v1.2.0**  
**Zielgruppe intern:** Marketing, Kommunikation, Produktmarketing, Presse  
**Verwendung:** Website, Broschüren, Messe, Social Media, Pressemitteilungen, Kampagnen-Briefings  
**Stand:** Juli 2026  

**Verwandte Dokumente:**  
[Add-on Sets & Vertrieb](./ANOMALYMATRIX_ADDON_SETS_VERTIEB.md) · [Anwendung & Einsatz](../PRODUCT_APPLICATION.md) · [Release v1.2.0](../RELEASE_NOTES_v1.2.0.md) · [Multi-Kamera](../MULTI_CAMERA.md)

---

## In 30 Sekunden — Elevator Pitch

**AnomalyMatrix** ist das **Inline-Qualitäts-Add-on** für bestehende Fertigungslinien: Es prüft Bauteile **automatisch auf Abweichungen vom Gut-Teil** — ohne jeden Fehlertyp vorab programmieren zu müssen. Das Ergebnis ist eine klare **Ampelentscheidung** (grün / gelb / rot), ein **Operator-HMI** für schnelle Entscheidungen am Band und eine **direkte SPS-Anbindung über OPC UA**. Mit **Multi-Kamera-Prüfung**, **Drift-Erkennung pro Kamera** und **Human-in-the-Loop-Feedback** erkennt AnomalyMatrix Probleme **bevor Serienfehler und Stillstände teuer werden**.

**Claim (Vorschlag):** *Qualität sehen, bevor sie teuer wird.*

---

## Die fünf USP — klar herausgestellt

Diese Punkte sind das **Kernversprechen** gegenüber klassischer Bildverarbeitung, manueller Sichtprüfung und generischer KI-Plattformen. In allen Marketing-Materialien sollten sie **sichtbar und wiedererkennbar** sein.

### USP 1 — Anomalie statt Regelprogrammierung

| Was | Warum es zählt |
|-----|----------------|
| Unüberwachtes Lernen auf **Gut-Teilen** (PatchCore) | Unbekannte und seltene Fehlerbilder werden erkannt, ohne dass jeder Defekt vorab modelliert werden muss |
| Anomalie-Score + Heatmap | Nachvollziehbare Bewertung statt „Black Box“ — Operator und QS sehen **wo** etwas auffällt |
| Rezept- und modellversioniert | Anpassung an Materialwechsel, Werkzeug, Chargen — ohne Neuprojekt |

**Marketing-Botschaft:** *„Sie müssen nicht jeden Fehler kennen — Sie müssen nur gute Teile kennen.“*

---

### USP 2 — Add-on für die bestehende Linie (nicht Neubau)

| Was | Warum es zählt |
|-----|----------------|
| Prüfstelle **an** die Linie, nicht **in** die Maschine | Geringes Integrationsrisiko, kurze Time-to-Value |
| Autonomer Installer (Ubuntu Server 24.04 LTS) | Produktiv in **Tagen**, nicht Monaten |
| Modulare Architektur (API, HMI, Edge, OPC-UA-Gateway) | Passt in OT-Umgebungen, skalierbar von Pilot bis Werk |

**Marketing-Botschaft:** *„Ihre Linie bleibt. Ihre Qualität wird schärfer.“*

---

### USP 3 — Qualität wird Teil der Maschine (OPC UA)

| Was | Warum es zählt |
|-----|----------------|
| OPC-UA-Gateway mit dokumentiertem NodeSet | SPS-Integration nach Industriestandard, nicht proprietär |
| Trigger, Stop, Reject, Acknowledge | Prüfung im **Linientakt** — automatisch oder manuell |
| Sign/Encrypt-fähig | OT-taugliche Sicherheitsanforderungen adressierbar |
| Contract v1.2 inkl. Multi-View & Drift-Nodes | Planbare Schnittstelle für Automatisierungsteams |

**Marketing-Botschaft:** *„Vom Score zur SPS-Reaktion — in unter 500 ms.“*

---

### USP 4 — Operator-first HMI (Tesla-inspiriert)

| Was | Warum es zählt |
|-----|----------------|
| Ampel, Score, letzte Inspektionen auf einen Blick | Entscheidung am Band in **Sekunden**, nicht Minuten |
| Inspektionsdetail mit Heatmap & Multi-View | Grenzfälle nachvollziehbar erklären |
| Trends & Drift **pro Kamera** | Prozessverschlechterung früh sichtbar — nicht erst beim Ausschuss |
| Hilfe & FAQ **DE/EN** im HMI | Kein Handbuch-Suchen in der Schicht |
| Konfiguration: Kameraauswahl 1–4 ohne IT | Prozessingenieur bedient die Prüfstelle selbst |

**Marketing-Botschaft:** *„Designed für den Band — nicht für das Büro.“*

---

### USP 5 — Human-in-the-Loop & Enterprise-Readiness

| Was | Warum es zählt |
|-----|----------------|
| QA-Feedback (bestätigen / falsch positiv / Nachprüfung) | System wird **besser für Ihre Linie** — nicht generischer |
| Modell-Training, Promotion, Rollback (< 60 s) | Kontrollierter Modell-Lifecycle ohne IT-Großprojekt |
| RBAC, Audit-Log, Domain-Events | Audit-fähig für regulierte Branchen |
| Production-Härtung, Backup/Restore, Runbook | Betrieb in 24/7-OT realistisch planbar |
| On-premise Standard, optional License Server | Keine Cloud-Pflicht — Daten bleiben im Werk |

**Marketing-Botschaft:** *„KI mit Verantwortung — Mensch und Maschine im gleichen Qualitätsprozess.“*

---

## Funktionsübersicht — vollständig nach Modul

Alle unten genannten Funktionen sind **heute in v1.2.0** verfügbar, sofern nicht als Roadmap gekennzeichnet.

### A) Inspektion & Anomalieerkennung

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **Gut-Teil-basierte Anomalieerkennung** | PatchCore-Inferenz auf Referenz-Gut-Teilen | Keine exhaustive Fehlerdefinition |
| **Anomalie-Score** | Numerische Bewertung pro Prüfung | Vergleichbar über Schichten und Chargen |
| **Ampelentscheidung** | Grün / Gelb / Rot aus Score & Rezept | Sofort verständlich für jeden Operator |
| **Heatmap** | Visuelle Hervorhebung auffälliger Bildbereiche | Erklärt „warum rot“ — senkt Black-Box-Einwände |
| **Performance-Ziel < 500 ms** | End-to-End-Zyklus (Capture → Infer → Publish) | Taktfähig an der Linie |
| **Rezepte** | Versionierte Prüfparameter (Beleuchtung, Schwellwerte, Modell) | Wiederholbar bei Variantenwechsel |
| **Inspektions-Historie** | Letzte Ergebnisse abrufbar & filterbar | Schichtübergabe und Nachverfolgung |

### B) Multi-Kamera Case-Prüfung *(Neu v1.2)*

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **Hardware-Discovery** | Automatische Erkennung angeschlossener Kameras (V4L2/USB) | Plug-and-Play ohne manuelle Gerätelisten |
| **Stationsauswahl 1–4** | Admin wählt bis zu vier Kameras für eine Prüfstelle | Mehrere Blickwinkel auf **denselben Case** |
| **Worst-View-Aggregation** | Gesamtentscheidung = schlechteste Sicht | Kein „blinder Fleck“ bei Mehrfachperspektive |
| **Multi-View im HMI** | Detailansicht zeigt alle Views | QA kann Grenzfälle vollständig beurteilen |
| **OPC-UA Multi-View** | LastResult mit CameraIds, ViewCount, WorstViewCameraId | SPS kennt das Gesamtergebnis und die schlechteste Kamera |
| **Filter pro Kamera** | Ergebnisabfrage nach `camera_id` | Feinanalyse je Perspektive |

> **Ehrliche Abgrenzung (Vertrieb/Marketing):** Capture erfolgt sequentiell — kein Hardware-Trigger-Sync. GigE/GenICam: Folgerelease.

### C) Prozessdrift & Trends *(Erweitert v1.2)*

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **Trend-Engine** | Gleitende Auswertung über Inspektionsfenster | Frühwarnung vor Serienfehlern |
| **Drift pro Kamera** | `by_camera[]`, `drifting_camera_id`, `drift_score` | **Gezielte** Wartung statt generischem Alarm |
| **Trend-Warnungen** | Severity, Reason, optional Kamera-Bezug | Proaktive Prozesskorrektur |
| **Observability-Summary** | KPIs für Betrieb und Management | Reporting ohne Excel-Nebenbuch |
| **OPC-UA Drift-Nodes** | DriftingCameraId, DriftScore, ScoreDelta an SPS | Automatisierung kann auf Drift reagieren |
| **Trends-Seite im HMI** | Tabellarische Drift je Kamera | Prozessingenieur sieht Verschlechterung sofort |

### D) Bilderfassung (Edge)

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **Edge-Acquisition-Service** | Dedizierter Capture-Dienst am Prüfort | Entkoppelt von Cloud und Büro-IT |
| **OpenCV / V4L2** | USB-Webcam und industrienahe Kameras | Einstieg mit Standard-Hardware |
| **Synthetic-Modus** | Demo/Pilot ohne physische Kamera | PoV ohne Hardware-Blocker |
| **Offline-Queue & Retry** | Puffer bei kurzzeitigen Capture-Fehlern | Robustheit im Schichtbetrieb |
| **Health-Endpoint** | Edge-Status für Monitoring | Transparenz für Instandhaltung |
| **CAMERA_SOURCES_JSON** | Mapping mehrerer Quellen | Flexible Stationskonfiguration |

### E) SPS-Integration (OPC UA)

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **OPC-UA-Server (Port 4840)** | Standardisierte Maschinenschnittstelle | Kein Vendor-Lock-in |
| **Trigger** | ExternalTrigger, StartInspection | Prüfung im Linientakt |
| **Reaktion** | StopLineRequest, RejectPart bei rot | Qualität steuert die Anlage |
| **AcknowledgeStop** | Sichere Wiederanlauf-Logik | OT-Sicherheit adressiert |
| **LastResult-Publish** | Pass/Fail, Score, DefectClass an SPS | Nahtlose Einbindung in Maschinenprogramm |
| **Sign/Encrypt** | PKI-fähige Kommunikation | Enterprise- und Kunden-Audit-tauglich |
| **Versionierte Contracts** | JSON-Schemas für Events & OPC-UA-Mapping | Planbare Integration für Automatisierung |

### F) Operator-HMI (Frontend)

| Seite | Funktionen | Marketing-Nutzen |
|-------|------------|------------------|
| **Dashboard** | Ampel, Score, letzte Inspektionen, Start | Schichtführer sieht Linie auf einen Blick |
| **Inspection Detail** | Einzelbild, Multi-View, Heatmap, QA-Aktionen | Nachvollziehbare Entscheidungen |
| **Trends** | KPIs, Drift je Kamera, Warnungen | Prozessstabilität über Schichten |
| **Konfiguration** | Kameraauswahl 1–4, Stationsparameter | Self-Service für Prozessingenieure |
| **Hilfe & FAQ** | Wissensbasis DE/EN | Geringere Schulungskosten |
| **Login & Rollen** | Sichere Anmeldung in Produktion | Trennung Operator / QA / Admin |

### G) Qualitätssicherung & Continual Learning

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **QA-Feedback** | Bestätigen, Falsch positiv, Nachprüfung | System lernt aus echten Fällen |
| **Audit-Log** | Wer hat wann was geändert/bewertet | Audit-Sicherheit |
| **Domain-Events** | InspectionCompleted, FeedbackSubmitted, … | Integration in MES/Analytics möglich |
| **Modell-Training** | Training aus Gut-Teil-Bildern (MinIO/lokal) | Kein separates ML-Tool nötig |
| **Promotion Gate** | Freigabe nur nach Validierung | Kein „Wild-West“-Modellwechsel |
| **Modell-Rollback** | Rückkehr zum Vorgängermodell < 60 s | Risikoarme Updates |

### H) Sicherheit & Enterprise

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **RBAC** | Operator, QA Lead, Prozessingenieur, Admin | Rollengerechte Bedienung |
| **JWT + Secure Session Cookie** | Keine Tokens in localStorage | OT-Sicherheitsbaseline |
| **Service-Auth-Token** | API ↔ Edge ↔ OPC-UA abgesichert | Schutz interner Dienste |
| **CORS-Allowlist & Rate-Limits** | Prod-Härtung gegen Missbrauch | IT/OT-Gespräche erleichtert |
| **Production Guards** | Startup-Checks in Prod-Umgebung | Kein versehentlicher Dev-Modus |
| **TLS-Overlay** | Compose-TLS / Reverse-Proxy vorbereitet | HTTPS für HMI |
| **Lizenzierung** | Lokal (AMX-Keys) oder Byte-Commander License Server | Skalierbare Lizenzverwaltung |

### I) Betrieb, Deployment & Daten

| Funktion | Beschreibung | Marketing-Nutzen |
|----------|--------------|------------------|
| **Docker Compose Stack** | API, HMI, Edge, OPC-UA, Postgres, optional Influx/MinIO | Standardisiertes Deployment |
| **Autonomer Installer** | One-Liner oder `.run`-Asset | Schnelle Inbetriebnahme vor Ort |
| **Health & Ready Endpoints** | `/health`, `/ready` (DB + Abhängigkeiten) | Monitoring & Orchestrierung |
| **Backup/Restore** | Postgres & Artefakte | Disaster Recovery |
| **Production Runbook** | Betrieb, Security, Rollout-Gates | Planbarer 24/7-Betrieb |
| **InfluxDB (optional)** | Metriken & Trends | Historische Auswertung |
| **MinIO (optional)** | Rohbilder, Heatmaps, Trainingsartefakte | Vollständige Bild-Dokumentation |

---

## Plattform-Architektur — für Marketing-Grafiken

```
┌─────────────────────────────────────────────────────────────────┐
│                     OPERATOR-HMI (Browser)                       │
│   Dashboard · Detail · Trends · Konfiguration · Hilfe DE/EN     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼────────────────────────────────────┐
│                      ANOMALYMATRIX API                           │
│  Inspektion · RBAC · Lizenz · Trends · QA · Observability       │
└──────┬──────────────────────┬──────────────────────┬────────────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│ Edge Capture │    │  OPC-UA Gateway │    │ Postgres / MinIO │
│ 1–4 Kameras  │    │ Trigger · Stop  │    │ Ergebnisse · ML  │
│ Discovery    │    │ Multi-View v1.2  │    │ Heatmaps · Audit │
└──────┬───────┘    └────────┬────────┘    └──────────────────┘
       │                     │
       ▼                     ▼
   [ Kamera ]           [ SPS / PLC ]
```

---

## Zielgruppen & Kernbotschaften

| Zielgruppe | Schmerzpunkt | AnomalyMatrix-Antwort | Key Message |
|------------|--------------|----------------------|-------------|
| **Produktionsleitung** | Ausschuss, Stillstand, späte Fehler | Früherkennung, messbare KPIs | „Weniger Serienfehler — ROI ab Woche 4–8.“ |
| **Operator / Schichtführer** | Stress, unklare Entscheidungen | Ampel-HMI, < 500 ms | „Grün, Gelb, Rot — sofort handeln.“ |
| **QS / QA Lead** | Audits, Falschmeldungen | Feedback, Audit, Trends | „Jede Entscheidung dokumentiert.“ |
| **Prozessingenieur** | Materialwechsel, Drift | Rezepte, Multi-Kamera-Drift, Modell-Lifecycle | „Prozess unter Kontrolle — pro Kamera.“ |
| **Automatisierung** | Integrationsaufwand | OPC UA, NodeSet, Contracts | „Standard-Schnittstelle — kein Sonderweg.“ |
| **IT / OT-Security** | Shadow-IT, Cloud-Zwang | On-premise, RBAC, Härtung | „OT-first — Daten bleiben im Werk.“ |
| **Einkauf / Management** | Unplanbare IT-Projekte | Add-on Sets, Installer | „Investierbar statt experimentell.“ |

---

## Branchen & Use Cases (Copy-Bausteine)

| Branche | Typische Prüfung | Headline-Idee |
|---------|------------------|---------------|
| **Automotive Zulieferer** | Naht, Oberfläche, Montage | „Nahtlose Qualität — ohne Naht-Blindheit.“ |
| **Elektronik & EMS** | Lötstelle, Bestückung, Label | „Jede Platine gesehen — jeder Fehler früh.“ |
| **Kunststoff & Spritzguss** | Grat, Farbe, Einfallstellen | „Chargenwechsel? Ihr Gut-Teil-Modell passt sich an.“ |
| **Metall & Blech** | Schweißnaht, Kratzer | „Vier Kameras, ein Case — kein blinder Fleck.“ |
| **MedTech / Pharma (Umfeld)** | Dokumentierte Inline-Prüfung | „Audit-ready — Human-in-the-Loop inklusive.“ |
| **Konsumgüter & Verpackung** | Druck, Etikett, Verschluss | „100-%-Check im Takt — ohne Extra-Personal.“ |

---

## Differenzierung — Wettbewerbsmatrix (Messaging)

| Dimension | Klassische Regel-CV | Manuelle Sichtprüfung | Generische Cloud-KI | **AnomalyMatrix** |
|-----------|--------------------|-----------------------|---------------------|-------------------|
| Unbekannte Fehler | Schwach | Abhängig von Person | Variabel | **Stark (Gut-Teil-Lernen)** |
| Integrationszeit | Mittel–hoch | Keine (aber teuer laufend) | Oft hoch (Cloud/IT) | **Niedrig (Add-on, Wochen)** |
| SPS-Anbindung | Projekt-spezifisch | Keine | Selten nativ | **OPC UA out-of-the-box** |
| Operator-Akzeptanz | Mittel | Hoch (aber ermüdend) | Niedrig | **Hoch (Ampel-HMI)** |
| Multi-Perspektive | Aufwendig | Ermüdend | Selten OT-tauglich | **1–4 Kameras, worst-view** |
| Drift-Erkennung | Begrenzt | Spät | Oft generisch | **Pro Kamera, an SPS** |
| Datenhoheit | On-premise möglich | Lokal | Cloud-lastig | **On-premise Standard** |
| Audit & QA-Loop | Variabel | Papier/Excel | Variabel | **Eingebaut** |

---

## Was ist neu in v1.2.0 — Kampagnen-Stichpunkte

Für Presse, Release-Mailings und Website-Updates:

1. **Multi-Kamera Case-Prüfung** — bis zu 4 Kameras prüfen denselben Case; schlechteste Sicht entscheidet.  
2. **Drift pro Kamera** — Prozessverschlechterung wird der **konkreten Kamera** zugeordnet, nicht nur dem Gesamtscore.  
3. **OPC-UA Contract v1.2** — Multi-View LastResult und Drift-Nodes für Automatisierung.  
4. **Byte-Commander License Server** — zentrale Lizenzverwaltung für Mehrstandort-Rollouts.  
5. **80 automatisierte Tests** — Production-ready Qualitätssicherung in CI.

**Presse-Zeile (Vorschlag):**  
*AnomalyMatrix v1.2.0 bringt Multi-Kamera-Inline-Prüfung und kameraweise Drift-Erkennung in bestehende Fertigungslinien — ohne Neubau, mit OPC-UA-Anbindung.*

---

## KPIs & ROI-Argumente (für Marketing & Sales Enablement)

| KPI | Was AnomalyMatrix liefert | Story für Management |
|-----|---------------------------|----------------------|
| **Anomaliequote** | Trend über Schichten | Frühwarnung vor Serienfehler |
| **Ausschuss-Rate** | Vergleich vor/nach Einführung | Direkte Materialersparnis |
| **Prüfzyklus p95** | < 500 ms Ziel | Taktfähigkeit gesichert |
| **Falsch-Positive-Rate** | QA-Feedback messbar | Weniger unnötige Stopps |
| **MTTR Qualitätsstörung** | Heatmap + Score + Historie | Schnellere Klärung am Band |
| **Audit-Abdeckung** | Events + Audit-Log | Geringeres Zertifizierungsrisiko |

---

## Messaging-Matrix — Kanäle

| Kanal | Fokus | Beispiel |
|-------|-------|----------|
| **Website Hero** | USP 1 + 2 | „Anomalieerkennung als Add-on für Ihre Linie.“ |
| **LinkedIn** | USP 4 + Drift | „Prozessdrift sichtbar — pro Kamera, pro Schicht.“ |
| **Messe-Stand** | Live-Ampel + Multi-View | Demo: 4 Kameras, ein Case, worst-view rot |
| **Presse** | v1.2.0 + OPC UA | „Inline-Qualität mit SPS-Standard“ |
| **Whitepaper** | USP 1 + Human-in-the-Loop | „Vom Gut-Teil zum lernenden Prüfsystem“ |
| **Case Study** | KPI + Branche | „−30 % Nacharbeit in 8 Wochen Pilot“ (Platzhalter — mit Kundendaten füllen) |

---

## Taglines & Claims (Vorschläge)

| Typ | Text |
|-----|------|
| **Haupt-Claim** | Qualität sehen, bevor sie teuer wird. |
| **Technisch** | Gut-Teil-Lernen. Ampel-Entscheidung. OPC UA. |
| **Operator** | Grün. Gelb. Rot. Weiter. |
| **Management** | Add-on statt Ausschuss. |
| **Multi-Kamera** | Vier Blickwinkel. Eine Entscheidung. |
| **Drift** | Drift erkennen, bevor die Serie kippt. |

---

## Ehrliche Abgrenzung — Vertrauen schaffen

In Marketing-Materialien ** aktiv nennen** — senkt Einwände und wirkt glaubwürdig:

| AnomalyMatrix **ist** | AnomalyMatrix **ist nicht** |
|-----------------------|----------------------------|
| Inline-Anomalieerkennung auf Gut-Teil-Basis | Ersatz für alle messenden Prüfungen (z. B. KMG) |
| Entscheidungs- und Dokumentationshilfe | Automatische Root-Cause-Analyse ohne Fachpersonal |
| Add-on für bestehende Linien | Kompletter Maschinen-Neubau |
| Konfigurierbare SPS-Reaktion | Rechtlich bindende QS-Freigabe |
| Sequentielle Multi-Kamera-Prüfung | Hardware-synchronisierte High-Speed-Multi-Cam (Roadmap) |

---

## Add-on Sets — Kurzverweis für Paket-Kommunikation

Details und Preislogik: [`ANOMALYMATRIX_ADDON_SETS_VERTIEB.md`](./ANOMALYMATRIX_ADDON_SETS_VERTIEB.md)

| Set | Einzeiler | USP-Fokus |
|-----|-----------|-----------|
| **Vision Start** | Erste Prüfstelle ohne SPS-Umbau | USP 1, 2, 4 |
| **Line Connect** | Qualität im Linientakt mit OPC UA | USP 2, 3 |
| **Quality Pro** | QA, Audit, Modell-Lifecycle | USP 5 |
| **Line Enterprise** | Mehrstandort, SLA, Rollout | USP 2, 5 + Skalierung |

---

## Checkliste für Marketing-Materialien

Vor Veröffentlichung prüfen:

- [ ] Alle **5 USP** mindestens einmal klar benannt  
- [ ] Version **v1.2.0** und Stand **Juli 2026**  
- [ ] Multi-Kamera (1–4) und **Drift pro Kamera** erwähnt, wenn technisch relevant  
- [ ] **On-premise** und **OPC UA** als Vertrauensanker  
- [ ] Abgrenzung (kein CMM-Ersatz, keine QS-Freigabe) bei B2B-Stücken  
- [ ] Performance-Ziel „unter 500 ms“ nur als **Zielwert**, nicht als Garantie  
- [ ] Screenshots/Demos: Ampel, Trends mit Kamera-Tabelle, Konfiguration  
- [ ] DE/EN: HMI ist bilingual — Marketing kann beides anspielen  

---

## Anhang — Feature-Checkliste v1.2.0 (technische Vollständigkeit)

Zum Abhaken in Produktmarketing und Presse-Fact-Sheets:

- [x] PatchCore-Anomalieerkennung  
- [x] Ampelentscheidung (grün/gelb/rot)  
- [x] Heatmap  
- [x] Multi-Kamera 1–4, worst-view  
- [x] Kamera-Hardware-Discovery  
- [x] Drift pro Kamera (API, HMI, OPC-UA)  
- [x] OPC-UA Trigger / Stop / Reject / Acknowledge  
- [x] OPC-UA Multi-View & Drift-Nodes (Contract v1.2)  
- [x] Operator-HMI (Dashboard, Detail, Trends, Config, Hilfe)  
- [x] QA-Feedback & Audit  
- [x] Modell Training / Promotion / Rollback  
- [x] RBAC & Login  
- [x] Lizenz lokal + License Server  
- [x] Docker Compose Production Stack  
- [x] Autonomer Installer  
- [x] Backup/Restore & Runbook  
- [ ] GigE/GenICam (Roadmap)  
- [ ] Hardware-Trigger-Sync Multi-Cam (Roadmap)  

---

**AnomalyMatrix** — *Qualität sehen, bevor sie teuer wird.*

*Dokumentversion: 1.0 · Stand: Juli 2026 · Basis: AnomalyMatrix v1.2.0*  
*Intern: Marketing & Kommunikation · Vertrieb: `ANOMALYMATRIX_ADDON_SETS_VERTIEB.md` · Technik: `docs/PRODUCT_APPLICATION.md`*
