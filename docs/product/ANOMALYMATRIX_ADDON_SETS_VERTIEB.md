# AnomalyMatrix Add-on Sets  
## Inline-Anomalieerkennung für bestehende Produktionslinien

**Produkt:** AnomalyMatrix v1.0  
**Zielgruppe:** Endkunden, Produktionsleiter, QS, Automatisierung, Einkauf  
**Verwendung:** Marketing, Vertrieb, Angebotsgrundlage, Messe & Kundengespräche  

---

## In 60 Sekunden verstanden

**AnomalyMatrix** ist ein **Add-on-Qualitätssystem** für Fertigungslinien: Es prüft Bauteile und Oberflächen **inline** auf Abweichungen vom Gut-Teil — **ohne** jeden Fehlertyp vorab programmieren zu müssen.

Statt klassischer Regel-basierter Bildverarbeitung lernt die Lösung aus **guten Referenzteilen** und meldet ungewöhnliche Muster als **Anomalie-Score** mit klarer **Ampelentscheidung** (grün / gelb / rot).

Das Ergebnis:

- **Frühere Fehlererkennung** — bevor Serienfehler entstehen  
- **Schnellere Entscheidung am Band** — Operator-HMI statt Rätselraten  
- **Direkte SPS-Anbindung** — Trigger, Stopp und Ausschleusen über **OPC UA**  
- **Nachvollziehbare Qualität** — Feedback, Audit und Trends für QS und Management  

AnomalyMatrix **ersetzt keine Linie** — es **erweitert** Ihre bestehende Anlage um eine intelligente Prüfstelle, die sich in wenigen Tagen integrieren lässt.

---

## Das Problem, das wir lösen

| Herausforderung in der Produktion | Folge | AnomalyMatrix-Antwort |
|-----------------------------------|-------|------------------------|
| Unbekannte oder seltene Fehlerbilder | Regel-CV deckt sie nicht ab | Unüberwachtes Lernen auf Gut-Teilen |
| Manuelle Sichtprüfung am Takt | Ermüdung, Inkonsistenz, Lücken | Automatische 100-%-Kontrolle an Engpässen |
| Späte Erkennung von Prozessdrift | Serienausschuss, Stillstand | Trend-Engine & Frühwarnungen |
| Getrennte Welten: Kamera, KI, SPS, QS | Integrationsprojekte dauern Monate | **Komplettes Add-on Set** aus einer Hand |
| Fehlende Dokumentation für Audits | Reibung mit Kunden & Zertifizierung | Audit-Log, Events, QA-Feedback |

---

## Für wen ist AnomalyMatrix?

| Rolle | Was Sie gewinnen |
|-------|------------------|
| **Operator / Schichtführer** | Ampel, Score, letzte Inspektionen — Entscheidung in Sekunden |
| **QS / QA Lead** | Feedback zu Falschmeldungen, Nachprüfungen, Audit-Spur |
| **Prozessingenieur** | Trends, Rezept- und Modellversion, Prozessdrift sichtbar |
| **Automatisierung / Instandhaltung** | OPC-UA-Schnittstelle, definierte PLC-Signale, dokumentiertes NodeSet |
| **Produktionsleitung** | Weniger Ausschuss, stabilere Linie, messbare KPIs |
| **Einkauf / Management** | Planbare Add-on-Investition statt Individualprojekt |

---

## Typische Einsatzgebiete

### Inline-Qualitätskontrolle (100-%-Prüfung)

Nach kritischen Prozessschritten:

- Kleben, Schweißen, Nieten, Crimpen  
- Lackieren, Beschichten, Drucken  
- Etikettieren, Montage, Verpacken  
- Oberflächen- und Nahtprüfung  

**Nutzen:** Jedes Teil wird bewertet — ohne den Linientakt zu sprengen.

### SPS-gesteuerte Automatisierung

- **Trigger:** Prüfung per SPS-Signal oder OPC-UA-Methode  
- **Reaktion bei rot:** Linie stoppen (`StopLineRequest`) oder Teil ausschleusen (`RejectPart`)  
- **Quittierung:** Sichere Wiederanlauf-Logik über `AcknowledgeStop`  

**Nutzen:** Qualität wird Teil der Maschinenlogik — nicht nur ein paralleles IT-System.

### Prozessüberwachung & Drift

- Gleitende Verschlechterung des Anomalie-Scores über Schichten  
- Frühwarnung vor Serienfehlern  
- KPIs: Anomaliequote, Zykluszeiten, OPC-UA-Publish-Rate  

**Nutzen:** Wartung und Parameterkorrektur **bevor** der Ausschuss explodiert.

### Qualitätssicherung & Continual Learning

- QA markiert Falsch-Positive und echte Defekte  
- Feedback fließt in Modellverbesserung und Audit  
- Grundlage für kontinuierliche Optimierung (Human-in-the-Loop)  

**Nutzen:** Das System wird mit der Zeit **besser für Ihre Linie** — nicht generischer.

---

## Warum Add-on Sets statt Einzelkomponenten?

Industriekunden wollen **kein Puzzle** aus Kamera, Software, Server, SPS-Schnittstelle und Schulung. Sie wollen:

1. **Planbare Integration** in eine **bestehende** Linie  
2. **Definierte Lieferumfänge** mit klaren Schnittstellen  
3. **Kurze Time-to-Value** — Pilot in Wochen, nicht Monaten  
4. **Skalierbarkeit** — von einer Prüfstelle auf mehrere Linien  

Unsere **Add-on Sets** sind deshalb **fertige Integrationspakete**: Hardware-Grundausstattung, Software-Stack, SPS-Anbindung, HMI, Inbetriebnahme und optional Support — abgestimmt auf den Reifegrad Ihrer Anlage.

---

# Add-on Set Übersicht

| Set | Kurzbeschreibung | Ideal für | Integrationstiefe |
|-----|------------------|-----------|-------------------|
| **Vision Start** | Erste Prüfstelle mit HMI, manuell oder halbautomatisch | Pilot, Machbarkeit, Lab/Linie | Software + Kamera + Edge |
| **Line Connect** | Vollständige SPS-Integration mit Trigger & Reaktion | Serienfertigung, Taktlinien | + OPC UA + PLC-Signale |
| **Quality Pro** | QS-Workflow, Feedback, Training, Audit | Regulierte Branchen, hohe QS-Anforderung | + RBAC, Feedback, Modell-Lifecycle |
| **Line Enterprise** | Mehrere Prüfstellen, Observability, Betrieb | Konzerne, mehrere Linien/Werke | + Skalierung, SLA, Rollout |

> **Hinweis für Vertrieb:** Alle Sets bauen auf derselben Software-Plattform (AnomalyMatrix v1.0) auf. Upgrades sind **Upgrade-Pfade**, keine Neuprojekte.

---

## Add-on Set 1 — **Vision Start**

### Positionierung

*„Sehen, bewerten, entscheiden — ohne SPS-Umbau.“*

Das Einstiegspaket für Kunden, die **schnell einen belastbaren Proof of Value** an der realen Linie brauchen: Kamera, Edge-Erfassung, KI-Bewertung und Operator-HMI — betrieben als Add-on neben der bestehenden Anlage.

### Lieferumfang (Standard)

| Kategorie | Inhalt |
|-----------|--------|
| **Software** | AnomalyMatrix Plattform (API, HMI, Inspektionspipeline) |
| **Edge-Erfassung** | Bildaufnahme-Service (Industriekamera oder USB/Webcam je nach Projekt) |
| **Inferenz** | PatchCore-basierte Anomalieerkennung auf Gut-Teil-Referenzen |
| **Operator-HMI** | Dashboard, Inspektionsdetail, Hilfe DE/EN |
| **Installation** | Autonomer Linux-Installer (Ubuntu Server 24.04 LTS empfohlen) |
| **Dokumentation** | Inbetriebnahme-Guide, Bedienhilfe im HMI |

### Typischer Integrationspunkt

```
[Bestehende Linie] → [Prüfstelle Add-on] → Operator startet Inspektion am HMI
                              ↓
                    Score + Ampel (grün/gelb/rot)
```

### Ideal wenn …

- Sie eine **Pilotstelle** ohne sofortigen SPS-Eingriff testen wollen  
- Prozessingenieure Rezepte und Schwellwerte kalibrieren  
- Management einen **sichtbaren ROI** vor größerer Automation braucht  

### Nicht enthalten (optional nachrüstbar)

- OPC-UA-Anbindung an SPS  
- Automatisches Stop/Ausschleusen  
- Multi-User-RBAC für große QS-Teams  

---

## Add-on Set 2 — **Line Connect**

### Positionierung

*„Qualität wird Teil der Maschine — Trigger, Stopp, Ausschleusen.“*

Das **Kernpaket für Produktionslinien**: Alles aus **Vision Start**, plus **OPC-UA-Gateway** mit dokumentiertem NodeSet für die SPS-Integration. Die Prüfung läuft **im Linientakt** — manuell am HMI oder vollautomatisch per PLC-Trigger.

**Hardware-Einkauf:** [`EINKAUFSLISTE_LINIE.md`](./EINKAUFSLISTE_LINIE.md)

### Lieferumfang (zusätzlich zu Vision Start)

| Kategorie | Inhalt |
|-----------|--------|
| **OPC-UA-Gateway** | Server (Port 4840), PLC-Bridge, Trigger-/Stop-Logik |
| **SPS-Signale** | u. a. `ExternalTrigger`, `StartInspection`, `StopLineRequest`, `RejectPart`, `AcknowledgeStop` |
| **Sicherheit** | Sign/Encrypt-fähige OPC-UA-Kommunikation (PKI nach Kundenanforderung) |
| **Automatisierung** | Inspektion aus SPS-Programm auslösbar; Ergebnis zurück an Anlage |
| **Inbetriebnahme** | Signal-Mapping-Workshop mit Automatisierung (1 Prüfstelle) |

### Typischer Integrationspunkt

```
[SPS / PLC] ←—— OPC UA ——→ [AnomalyMatrix Add-on]
     │                              │
 Trigger (Teil im Prüffeld)    Capture → Infer → Ampel
     │                              │
 Stop / Reject bei rot ←—— Publish —┘
```

### Ideal wenn …

- **100-%-Kontrolle im Takt** gefordert ist  
- Qualitätsentscheidungen **ohne Operator-Eingriff** erfolgen sollen  
- Bestehende Linie **nicht ersetzt**, sondern **erweitert** werden soll  

### Typische Reaktionslogik

| Ampel | Score (Richtwert) | Empfohlene Anlagenreaktion |
|-------|-------------------|----------------------------|
| **Grün** | niedrig | Teil weiter, Prozess normal |
| **Gelb** | mittel | Nachprüfung, Markierung, Sammelstelle |
| **Rot** | hoch | Stopp oder Ausschleusen (konfigurierbar) |

> Schwellwerte sind **rezeptabhängig** und werden in der Inbetriebnahme mit dem Kunden abgestimmt.

---

## Add-on Set 3 — **Quality Pro**

### Positionierung

*„Vom Alarm zur verbesserten Linie — mit QA, Audit und Modell-Lifecycle.“*

Für Kunden mit **hohen QS-Anforderungen**, Audit-Pflicht oder dem Wunsch, das System **kontinuierlich zu verbessern**. Baut auf **Line Connect** auf und aktiviert Rollen, Feedback-Schleife, Training und revisionssichere Nachverfolgung.

### Lieferumfang (zusätzlich zu Line Connect)

| Kategorie | Inhalt |
|-----------|--------|
| **Rollen & Rechte** | Operator, QA Lead, Prozessingenieur, Admin (RBAC) |
| **QA-Feedback** | Bestätigen, Falsch positiv, Nachprüfung — direkt im HMI |
| **Audit & Events** | Prüfprotokoll, Domain-Events, Rückverfolgbarkeit |
| **Modell-Lifecycle** | Training, Promotion, Rollback (< 60 s) |
| **Trends & KPIs** | Anomaliequote, Drift-Warnungen, Observability-Summary |
| **Persistenz** | PostgreSQL, optional InfluxDB & MinIO für Metriken/Heatmaps |
| **Schulung** | Operator + QA + Ingenieur (je 0,5–1 Tag, vor Ort oder remote) |

### Ideal wenn …

- **IATF, ISO, Kunden-Audits** dokumentierte Prüfprozesse verlangen  
- Falschmeldungen **systematisch reduziert** werden sollen  
- Prozessingenieure Modelle **ohne IT-Projekt** wechseln wollen  
- Mehrere Rollen **gleichzeitig** am System arbeiten  

### Human-in-the-Loop — so wird das System besser

1. Operator sieht Ampel und Score am Band  
2. QA bewertet auffällige Fälle (echter Defekt vs. Falschmeldung)  
3. Feedback fließt in Training und Trend-Auswertung  
4. Neues Modell wird geprüft, freigegeben und produktiv geschaltet  

**Kundennutzen:** Weniger Rauschen, höhere Akzeptanz am Band, nachweisbare Verbesserung über Zeit.

---

## Add-on Set 4 — **Line Enterprise**

### Positionierung

*„Vom Pilot zur unternehmensweiten Qualitätsplattform.“*

Das **Premium-Paket** für mehrere Prüfstellen, Werke oder Linien mit einheitlicher Architektur, Betriebs-SLA und Rollout-Begleitung. Alle Funktionen aus **Quality Pro**, plus Skalierung, Enterprise-Services und Executive-Reporting.

### Lieferumfang (zusätzlich zu Quality Pro)

| Kategorie | Inhalt |
|-----------|--------|
| **Skalierung** | Mehrere Kameras / Rezepte / Linien auf einer Plattform |
| **Enterprise-Betrieb** | Production-Härtung, Backup/Restore, Runbook, systemd-Autostart |
| **Sicherheit** | Service-Auth, JWT/Session, CORS, Rate-Limits, Secrets-Rotation |
| **Rollout** | Staged Deployment (Pilot → Linie → Werk) |
| **Support** | SLA nach Vereinbarung (Reaktionszeit, Updates, Remote-Support) |
| **Reporting** | Management-KPIs: Anomaliequote, Zyklus-p95, Trend-Severity |
| **Optional** | Multi-Site-Konzept, zentrale Lizenzverwaltung, Custom Branding HMI |

### Ideal wenn …

- **Mehrere Werke** dieselbe Lösung einführen wollen  
- IT/OT-Sicherheit **enterprise-tauglich** sein muss  
- Ein **langfristiger Partner** für Betrieb und Weiterentwicklung gesucht wird  

---

# Integration in bestehende Produktionslinien

## Grundprinzip: Add-on statt Ersatz

AnomalyMatrix wird **an** die Linie gehängt — nicht **in** sie hineinprogrammiert (außer der gewünschten SPS-Logik):

```
┌─────────────────────────────────────────────────────────────┐
│  BESTEHENDE LINIE (unverändert im Kern)                      │
│  Zuführung → Prozess → Handling → …                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ Prüfposition (neu)
                           ▼
              ┌────────────────────────────┐
              │  ANOMALYMATRIX ADD-ON SET │
              │  Kamera → KI → HMI → OPC UA │
              └─────────────┬──────────────┘
                            │ Signale
                            ▼
              ┌────────────────────────────┐
              │  SPS (Trigger / Stop / OK)  │
              └────────────────────────────┘
```

## Typische Einbauszenarien

| Szenario | Beschreibung | Empfohlenes Set |
|----------|--------------|-----------------|
| **Nacharbeitsinsel** | Manuelle oder halbautomatische Prüfstation neben der Linie | Vision Start |
| **Inline nach Prozess** | Kamera im Takt, SPS gibt Freigabe | Line Connect |
| **Vor Versand / Endkontrolle** | 100-%-Check mit QA-Feedback | Quality Pro |
| **Werkübergreifend** | Standardisierte Qualitätsplattform | Line Enterprise |

## Schnittstellen — was der Kunde mitbringen muss

| Thema | Kundenseite | AnomalyMatrix liefert |
|-------|-------------|----------------------|
| **Mechanik** | Halterung, Beleuchtung, Prüfposition | Spezifikation & Abstimmung |
| **Elektrik** | 24 V, Netzwerk, ggf. Trigger-Eingang | Edge-PC / Industrial PC im Set |
| **SPS** | OPC-UA-fähige Steuerung oder Gateway | NodeSet, Signal-Mapping, Bridge |
| **Netzwerk** | VLAN, Firewall-Regeln OT | Installations- & Sicherheits-Guide |
| **Referenzteile** | Gut-Teile für Modell-Training | Training-Workflow im System |

## Time-to-Value (Richtwerte)

| Phase | Dauer (typisch) | Ergebnis |
|-------|-----------------|----------|
| Kick-off & Abstimmung | 1–2 Wochen | Anforderungen, Prüfposition, Set-Auswahl |
| Mechanik & Kamera | 1–3 Wochen | Bildqualität, Beleuchtung, Rezept |
| Software-Installation | 1 Tag | Laufende Plattform (Installer oder Vor-Ort) |
| SPS-Integration | 1–2 Wochen | Trigger & Reaktion im Takt |
| Kalibrierung & Abnahme | 1–2 Wochen | Schwellwerte, Abnahmeprotokoll |
| **Pilot produktiv** | **ca. 4–8 Wochen** | Messbare erste KPIs |

> Abhängig von Beleuchtung, Takt, SPS-Projekt und Verfügbarkeit von Gut-Teilen.

---

# Was der Endanwender im Alltag sieht

## Operator-HMI (Ampel-Logik)

Das HMI ist **operator-first** — groß, klar, schnell:

- **Dashboard:** Letzte Inspektionen, Ampel, Score, Prüfung starten  
- **Detail:** Einzelbild, Heatmap-Vorschau, Entscheidung nachvollziehen  
- **Trends:** Verschlechterung über Schichten erkennen  
- **Hilfe DE/EN:** Eingebaute Wissensbasis — kein Handbuch-Suchen  

## Typischer Schichtablauf

1. Linie startet — SPS triggert Inspektion **oder** Operator startet manuell  
2. Bild wird erfasst, Modell bewertet in **unter 500 ms** (Zielwert)  
3. Ampel erscheint am HMI und an der SPS  
4. Bei rot: Stopp/Ausschleusen gemäß Maschinenprogramm  
5. QA prüft Grenzfälle und hinterlässt Feedback  
6. Schichtende: Trends zeigen, ob der Prozess stabil blieb  

---

# Messbarer Nutzen — KPIs für Management & Vertrieb

| KPI | Was gemessen wird | Business-Effekt |
|-----|-------------------|-----------------|
| **Anomaliequote** | Anteil auffälliger Teile | Frühwarnung vor Serienfehlern |
| **Ausschuss-Rate** | Nach Einführung vs. Baseline | Direkte Materialersparnis |
| **Prüfzyklus (p95)** | Zeit pro Inspektion | Taktfähigkeit der Add-on-Stelle |
| **Falsch-Positive-Rate** | QA-Feedback „Falschmeldung“ | Weniger unnötige Stopps |
| **MTTR Qualitätsstörung** | Zeit bis Klärung | Weniger ungeplante Stillstände |
| **Audit-Abdeckung** | Dokumentierte Prüfungen | Weniger Audit-Risiko |

**Vertriebsargument:** Add-on Sets sind **investierbar**, weil KPIs **ab Woche 4–8** sichtbar werden — nicht erst nach einem Jahres-IT-Projekt.

---

# Technische Vertrauensbasis (für IT/OT-Gespräche)

Kurz und kundenverständlich — Details on demand:

| Thema | Aussage |
|-------|---------|
| **Architektur** | Modular: API, HMI, Edge, OPC-UA-Gateway, Datenbank |
| **Deployment** | Docker-basiert, autonomer Installer für Ubuntu Server 24.04 LTS |
| **SPS** | OPC UA, Machine-Vision-Companion-orientiertes NodeSet |
| **Sicherheit** | RBAC, JWT/Session, Service-Auth, Production-Härtung |
| **Daten** | Prüfergebnisse, Audit, optional Metriken & Heatmap-Speicher |
| **Verfügbarkeit** | systemd-Autostart, Backup/Restore, Production-Runbook |

---

# Abgrenzung — ehrlich und verkaufsstark

AnomalyMatrix ist **kein Wundermittel** — und das macht es glaubwürdig:

| AnomalyMatrix ist … | AnomalyMatrix ist nicht … |
|---------------------|---------------------------|
| Inline-Anomalieerkennung auf Gut-Teil-Basis | Ersatz für alle messenden Prüfungen (z. B. Toleranz-CMM) |
| Entscheidungs- und Dokumentationshilfe | Automatische Root-Cause-Analyse ohne Fachpersonal |
| Add-on für bestehende Linien | Kompletter Maschinen-Neubau |
| Konfigurierbare SPS-Reaktion | Rechtlich bindende QS-Freigabe (bleibt bei Ihnen) |

**Vertriebs-Tipp:** Diese Abgrenzung **senkt Einwände** und positioniert uns als **spezialisierten Qualitäts-Add-on-Partner**.

---

# Paketvergleich — Schnellübersicht für Angebote

| Leistung | Vision Start | Line Connect | Quality Pro | Line Enterprise |
|----------|:------------:|:------------:|:-----------:|:---------------:|
| Kamera & Edge-Erfassung | ✓ | ✓ | ✓ | ✓ |
| Operator-HMI | ✓ | ✓ | ✓ | ✓ |
| PatchCore-Inferenz | ✓ | ✓ | ✓ | ✓ |
| OPC-UA / SPS-Trigger | — | ✓ | ✓ | ✓ |
| Stop / Reject-Signale | — | ✓ | ✓ | ✓ |
| RBAC & Login | Basis | ✓ | ✓ | ✓ |
| QA-Feedback | — | optional | ✓ | ✓ |
| Modell Training / Rollback | — | optional | ✓ | ✓ |
| Audit & Events | — | optional | ✓ | ✓ |
| Trends & Observability | Basis | ✓ | ✓ | ✓ |
| Multi-Stelle / Multi-Linie | — | — | optional | ✓ |
| Enterprise-SLA & Rollout | — | — | — | ✓ |

---

# Branchen & Anwendungsbeispiele

| Branche | Typische Prüfung | Add-on Set |
|---------|------------------|------------|
| **Automotive Zulieferer** | Naht, Oberfläche, Montage | Line Connect / Quality Pro |
| **Elektronik & EMS** | Lötstellen, Bestückung, Label | Line Connect |
| **Kunststoff & Spritzguss** | Grat, Farbe, Einfallstellen | Vision Start → Line Connect |
| **Metall & Blech** | Schweißnaht, Kratzer, Form | Line Connect |
| **MedTech / Pharma (Umfeld)** | Dokumentierte Inline-Prüfung | Quality Pro |
| **Konsumgüter & Verpackung** | Druck, Etikett, Verschluss | Vision Start / Line Connect |

---

# Services & optionale Erweiterungen

| Service | Beschreibung |
|---------|--------------|
| **Inbetriebnahme vor Ort** | Mechanik-Abstimmung, Beleuchtung, Erstkalibrierung |
| **SPS-Workshop** | Signal-Mapping, Trigger-Logik, Abnahme mit Automatisierung |
| **Schulung** | Operator, QA, Ingenieur — rollenspezifisch |
| **Modell-Training Begleitung** | Gut-Teil-Sets, Promotion, Schwellwert-Feinjustierung |
| **Wartungsvertrag** | Updates, Remote-Support, Health-Checks |
| **Custom Rezept-Paket** | Weitere Bauteilvarianten / Kameras |
| **PKI / OPC-UA-Zertifikate** | Kundenspezifische Trust-Stores |

---

# Häufige Kundenfragen (FAQ)

**Brauchen wir eine neue Linie?**  
Nein. AnomalyMatrix ist explizit als **Add-on** für **bestehende** Linien konzipiert.

**Funktioniert das mit unserer SPS?**  
Ja, wenn OPC UA verfügbar ist (nativ oder über Gateway). Set **Line Connect** liefert das NodeSet und die Bridge.

**Wie lange dauert ein Pilot?**  
Typisch **4–8 Wochen** bis zur produktiven Pilotstelle — abhängig von Mechanik und SPS.

**Was passiert bei Material- oder Werkzeugwechsel?**  
Rezepte und Modelle sind versioniert. Prozessingenieure können trainieren, freigeben und bei Bedarf rollbacken.

**Ersetzt das unsere QS-Freigabe?**  
Nein. AnomalyMatrix **unterstützt** QS mit Daten, Feedback und Audit — die Freigabe bleibt in Ihrer Organisation.

**Können Operatoren das ohne IT-Kenntnisse bedienen?**  
Ja. Das HMI ist für den Schichtbetrieb designed — Ampel, Score, klare Aktionen, Hilfe in DE/EN.

**Ist das cloud-pflichtig?**  
Nein. Standard-Deployment **on-premise** auf Industrial PC / Server in Ihrem OT-Netz.

**Wie skalieren wir auf mehrere Linien?**  
Über **Quality Pro** und **Line Enterprise** — gleiche Plattform, weitere Kameras/Rezepte, zentraler Betrieb.

---

# Gesprächsleitfaden für Vertrieb

## Discovery-Fragen

1. Wo entsteht heute **Ausschuss** oder **Spätausschuss**?  
2. Gibt es **100-%-Prüfung** — manuell oder gar nicht?  
3. Wie ist die **SPS** angebunden (OPC UA vorhanden)?  
4. Wer trifft heute die **Qualitätsentscheidung** am Band?  
5. Was kostet ein **Stillstand** oder **Sortieraktion** pro Vorfall?  

## Einwandbehandlung

| Einwand | Antwort |
|---------|---------|
| „Wir haben schon Vision.“ | „Regel-CV findet bekannte Fehler. Wir finden **unbekannte** Abweichungen — ergänzend, nicht ersetzend.“ |
| „KI ist Black Box.“ | „Score, Heatmap, QA-Feedback — nachvollziehbar. Kein blindes Vertrauen.“ |
| „Integration dauert ewig.“ | „Add-on Set mit Installer und OPC-UA-Bridge — **Wochen**, nicht Monate.“ |
| „Operator akzeptieren das nicht.“ | „Ampel-HMI, unter 500 ms, Hilfe am Bildschirm — designed für den Band.“ |

## Nächster Schritt (CTA)

1. **Kostenlose Linie-Assessment** (1 h remote): Prüfposition, SPS, Set-Empfehlung  
2. **Vision Start Pilot** an einer definierten Station  
3. **Upgrade zu Line Connect** nach messbarem PoV  

---

# Kontakt & Angebotsstruktur

Für individuelle Angebote benötigen wir:

- Foto/Skizze der **Prüfposition**  
- **Taktzeit** und Teilevarianten  
- **SPS-Typ** und OPC-UA-Verfügbarkeit  
- Gewünschtes **Add-on Set** (oder Assessment)  
- Branche & **Audit-Anforderungen**  

---

**AnomalyMatrix** — *Qualität sehen, bevor sie teuer wird.*

*Dokumentversion: 1.0 · Stand: Juli 2026 · Basis: AnomalyMatrix v1.0.0*  
*Intern: Vertrieb & Marketing · Technische Details: `docs/PRODUCT_APPLICATION.md`, `docs/INSTALLATION.md`*
