/**
 * AnomalyMatrix Hilfe — nur Endanwender (Operator, QA, Ingenieur)
 * Fokus: Bedienung und Funktionen im HMI, keine Installation/IT
 */

export const HELP_CATEGORIES = [
  { id: 'application', label: 'Anwendung & Einsatz', icon: '🏭' },
  { id: 'start', label: 'Einstieg', icon: '🚀' },
  { id: 'screens', label: 'Bildschirme', icon: '🖥️' },
  { id: 'workflow', label: 'Arbeitsabläufe', icon: '🔄' },
  { id: 'roles', label: 'Rollen', icon: '👤' },
  { id: 'decisions', label: 'Bewertung & KPIs', icon: '📊' },
  { id: 'faq', label: 'Häufige Fragen', icon: '❓' },
  { id: 'glossary', label: 'Glossar', icon: '📖' },
];

export const HELP_ARTICLES = [
  {
    id: 'what-is-anomalymatrix',
    category: 'application',
    title: 'Wofür ist AnomalyMatrix?',
    keywords: ['anwendung', 'zweck', 'einsatz', 'nutzen', 'software', 'qualität', 'vision'],
    summary: 'Automatische Anomalieerkennung an der Produktionslinie — mit Operator-HMI, SPS-Anbindung und Qualitäts-Feedback.',
    featured: true,
    sections: [
      {
        heading: 'Kernaufgabe',
        paragraphs: [
          'AnomalyMatrix prüft Bauteile und Oberflächen an der Linie auf Abweichungen vom definierten Gut-Teil — ohne dass jeder mögliche Fehler vorher einzeln programmiert werden muss.',
          'Die Software lernt aus „guten“ Referenzen und meldet ungewöhnliche Muster als Anomalie-Score mit Ampelentscheidung (grün / gelb / rot).',
          'Ziel: Fehler früh erkennen, Ausschuss reduzieren und den Prozess stabil halten.',
        ],
      },
      {
        heading: 'Typische Einsatzgebiete',
        paragraphs: [
          'Inline-Qualitätskontrolle nach Bearbeitung, Kleben, Schweißen, Beschichten oder Montage.',
          '100-%-Kontrolle an Engpässen, wo manuelle Sichtprüfung zu langsam oder zu unzuverlässig ist.',
          'Nachrüstung an bestehenden Zellen über OPC UA — Trigger und Stop-Signale an die SPS.',
          'Trendüberwachung: Prozessdrift erkennen, bevor serienweise Fehlteile entstehen.',
          'Dokumentation und Feedback für QS: Bewertungen fließen in Audit und Modellverbesserung ein.',
        ],
      },
      {
        heading: 'Was die Software konkret leistet',
        paragraphs: [
          'Inspektion auslösen (manuell im Dashboard, automatisch per SPS-Trigger oder OPC-UA-Methode).',
          'Bild erfassen, mit KI-Modell bewerten, Ergebnis speichern und an die Anlage melden.',
          'Bei rot: Stop- und Ausschleus-Signale an die SPS (StopLineRequest, RejectPart).',
          'Operator-HMI: letzte Prüfungen, Detail mit Score und Heatmap.',
          'QA-Feedback: Anomalie bestätigen, falsch positiv markieren oder Nachprüfung anfordern.',
          'Trends und KPIs: Anomaliequote, Zykluszeiten, OPC-UA-Fehlerrate.',
        ],
      },
      {
        heading: 'Für wen ist es gedacht?',
        paragraphs: [
          'Operator: Prüfung starten, Ampel lesen, bei Auffälligkeiten reagieren.',
          'QA Lead: Ergebnisse bewerten, Feedback für kontinuierliche Verbesserung.',
          'Prozessingenieur: Trends und Rezept-/Modellversionen beobachten.',
          'Instandhaltung / Automatisierung: OPC-UA-Schnittstelle in die SPS-Logik einbinden.',
        ],
      },
      {
        heading: 'Was AnomalyMatrix nicht ersetzt',
        paragraphs: [
          'Kein Ersatz für werksverbindliche Freigabe- und Sperrprozesse — diese bleiben in Ihrer QS-Organisation.',
          'Kein vollautomatisches Root-Cause-Tool: Es liefert Hinweise (Score, Heatmap, DefectClass), die Fachpersonal einordnet.',
          'Messtechnische Einzelprüfung (z. B. Toleranzbemaßung) nur, wenn im Rezept und Modell vorgesehen.',
        ],
      },
    ],
    related: ['use-case-inline-qc', 'use-case-plc-automation', 'plc-opcua-signals', 'operator-daily-flow'],
  },
  {
    id: 'use-case-inline-qc',
    category: 'application',
    title: 'Inline-Qualitätskontrolle an der Linie',
    keywords: ['inline', 'linie', '100 prozent', 'kontrolle', 'ausschuss'],
    summary: 'Jedes Teil prüfen, ohne den Takt zu sprengen.',
    sections: [
      {
        heading: 'Szenario',
        paragraphs: [
          'Nach einem Prozessschritt (z. B. Naht, Beschichtung, Etikett) soll jedes Teil geprüft werden.',
          'Die SPS gibt das Teil frei oder stoppt die Linie bei rot.',
        ],
      },
      {
        heading: 'Nutzen',
        paragraphs: [
          'Konsistente Bewertung statt stichprobenartiger manueller Kontrolle.',
          'Sofortige Reaktion: Stop-Signal bei klarer Anomalie.',
          'Nachvollziehbare Historie jeder Inspektion (ID, Zeit, Score, Entscheidung).',
        ],
      },
      {
        heading: 'Typischer Ablauf',
        paragraphs: [
          'Teil positioniert → SPS setzt ExternalTrigger → Inspektion läuft → Ergebnis an SPS.',
          'Grün: Transport weiter. Rot: Stop, Teil gesperrt, QA informieren.',
        ],
      },
    ],
    related: ['what-is-anomalymatrix', 'decision-colors', 'plc-opcua-signals'],
  },
  {
    id: 'use-case-process-monitoring',
    category: 'application',
    title: 'Prozessüberwachung & Drift',
    keywords: ['drift', 'trend', 'prozess', 'frühwarnung', 'wartung'],
    summary: 'Langsame Verschlechterung erkennen, bevor die Serie kippt.',
    sections: [
      {
        heading: 'Szenario',
        paragraphs: [
          'Verschleiß, Medienwechsel oder Parameterabweichung führen zu schleichend steigenden Anomalie-Scores.',
          'Einzelne gelbe oder rote Teile sind noch kein Drama — der Trend ist es.',
        ],
      },
      {
        heading: 'Nutzen',
        paragraphs: [
          'Trends-Seite und Dashboard-KPIs zeigen Durchschnitt und Anomaliequote.',
          'Frühwarnung für Wartung oder Prozesskorrektur vor Massenausschuss.',
          'Vergleich über Schichten und Rezeptversionen möglich.',
        ],
      },
    ],
    related: ['trends-overview', 'engineer-trends-flow', 'what-is-anomalymatrix'],
  },
  {
    id: 'use-case-plc-automation',
    category: 'application',
    title: 'Automatisierung mit der SPS',
    keywords: ['automatisierung', 'sps', 'opc', 'trigger', 'stop'],
    summary: 'Prüfung und Reaktion ohne manuellen Eingriff am HMI.',
    sections: [
      {
        heading: 'Szenario',
        paragraphs: [
          'Die SPS steuert Takt, Kamera-Trigger und Transport — AnomalyMatrix ist die Bewertungsinstanz.',
        ],
      },
      {
        heading: 'Nutzen',
        paragraphs: [
          'Kein separater Bedienschritt für jede Inspektion nötig.',
          'Einheitliche Signale: Busy, ResultReady, DecisionCode, StopLineRequest.',
          'Quittierung über AcknowledgeStop für sichere Wiederanlauf-Logik.',
        ],
      },
    ],
    related: ['plc-opcua-signals', 'what-is-anomalymatrix'],
  },
  {
    id: 'use-case-quality-loop',
    category: 'application',
    title: 'Qualitätssicherung & kontinuierliche Verbesserung',
    keywords: ['qa', 'feedback', 'lernen', 'audit', 'dokumentation'],
    summary: 'Menschliche Expertise in die Software zurückführen.',
    sections: [
      {
        heading: 'Szenario',
        paragraphs: [
          'Das Modell meldet Anomalien — QA entscheidet, ob es echte Defekte oder Falschmeldungen sind.',
        ],
      },
      {
        heading: 'Nutzen',
        paragraphs: [
          'Feedback (bestätigen / falsch positiv / Nachprüfung) dokumentiert die QS-Entscheidung.',
          '„Anomalie bestätigt“ setzt die Prüfung auf n.i.O. (rot) und speichert das Bild als n.i.O.-Muster.',
          'Audit-Log und Events für Nachvollziehbarkeit bei Audits.',
        ],
      },
    ],
    related: ['qa-review-flow', 'what-is-anomalymatrix', 'glossary-feedback-verdict'],
  },
  {
    id: 'help-using-help',
    category: 'start',
    title: 'Hilfe nutzen',
    keywords: ['hilfe', 'suche', 'f1', 'faq', 'anleitung'],
    summary: 'So finden Sie Antworten direkt in der Oberfläche.',
    sections: [
      {
        heading: 'Navigation',
        paragraphs: [
          'Tab „Hilfe & FAQ“ öffnet die vollständige Wissensdatenbank.',
          'Der Hilfe-Button (?) unten rechts startet eine Schnellsuche.',
          'Taste F1 öffnet dieselbe Schnellhilfe; Esc schließt sie.',
        ],
      },
      {
        heading: 'Kontext-Hilfe',
        paragraphs: [
          'Auf Dashboard, Inspection Detail, Trends und Configuration: Link „Hilfe zu diesem Bereich“.',
          'Dort springen Sie direkt zum passenden Thema für den aktuellen Bildschirm.',
        ],
      },
      {
        heading: 'Suche',
        paragraphs: [
          'Stichwörter eingeben, z. B. „Feedback“, „rot“, „Trend“, „Lizenz“, „Pipeline“.',
          'Kategorien links schränken die Liste ein.',
        ],
      },
    ],
    related: ['hmi-overview', 'operator-daily-flow'],
  },
  {
    id: 'hmi-overview',
    category: 'start',
    title: 'Überblick über die Oberfläche',
    keywords: ['oberfläche', 'navigation', 'tabs', 'start', 'einstieg'],
    summary: 'Die wichtigsten Bereiche der AnomalyMatrix-Oberfläche.',
    sections: [
      {
        heading: 'Hauptnavigation',
        paragraphs: [
          'Dashboard — Prüfungen starten und letzte Ergebnisse sehen.',
          'Inspection Detail — Einzelprüfung mit Score, Heatmap und QA-Feedback.',
          'Trends — Verlauf und Kennzahlen über mehrere Prüfungen.',
          'Configuration — Aktives Rezept, Modell und Lizenzstatus (nur Anzeige).',
          'Hilfe & FAQ — diese Wissensdatenbank.',
        ],
      },
      {
        heading: 'Verbindungsstatus',
        paragraphs: [
          'Unter dem Titel sehen Sie, ob die Prüfungssoftware verbunden ist.',
          '„Backend verbunden“ — Live-Daten von der Anlage.',
          '„Offline-Seed-Daten“ — Demo-/Ersatzdaten; neue Prüfungen sind ggf. nicht möglich. IT oder Schichtleitung informieren.',
        ],
      },
    ],
    related: ['operator-daily-flow', 'dashboard-overview'],
  },
  {
    id: 'operator-daily-flow',
    category: 'workflow',
    title: 'Typischer Ablauf für Operatoren',
    keywords: ['operator', 'schicht', 'ablauf', 'prüfung', 'täglich'],
    summary: 'Vom Prüfstart bis zur Meldung an QA.',
    sections: [
      {
        heading: 'Schritt für Schritt',
        paragraphs: [
          '1. Dashboard öffnen und Linienstatus prüfen (grün = bereit).',
          '2. „Run Inspection Pipeline“ starten und auf die Meldung warten.',
          '3. Ergebnis in „Latest inspections“ prüfen — Farbe und Uhrzeit beachten.',
          '4. Bei amber oder rot: Zeile anklicken → Inspection Detail öffnen.',
          '5. Rot oder unklar: QA / Schichtleitung hinzuziehen; Teil ggf. sperren laut Werksregel.',
        ],
      },
      {
        heading: 'Bei grün',
        paragraphs: [
          'Teil kann weiterlaufen, sofern keine zusätzliche Werksvorschrift greift.',
          'Trends regelmäßig im Blick behalten — einzelnes Grün heißt nicht automatisch stabiler Prozess.',
        ],
      },
    ],
    related: ['dashboard-overview', 'decision-colors', 'pipeline-messages'],
  },
  {
    id: 'qa-review-flow',
    category: 'workflow',
    title: 'QA: Prüfung bewerten & Feedback',
    keywords: ['qa', 'qualität', 'feedback', 'review', 'falsch positiv'],
    summary: 'So dokumentieren Sie Ihre Einschätzung zu einer Inspektion.',
    sections: [
      {
        heading: 'Wann Feedback geben?',
        paragraphs: [
          'Nach visueller oder messtechnischer Nachprüfung des Teils.',
          'Besonders wichtig bei n.i.O. (rot) und Nachprüfung (gelb).',
          'Auch bei i.O., wenn Sie einen verdeckten Fehler vermuten.',
        ],
      },
      {
        heading: 'Feedback senden',
        paragraphs: [
          'Inspection Detail öffnen → Abschnitt „QA-Feedback“.',
          'Verdict wählen: Anomalie bestätigt, Falsch positiv oder Nachprüfung nötig.',
          'Optional Kommentar (z. B. Fehlerstelle, Batch, Schicht).',
          '„Feedback senden“ — bei Erfolg erscheint „Feedback gespeichert.“',
        ],
      },
      {
        heading: 'Wirkung',
        paragraphs: [
          '„Anomalie bestätigt“ zeigt die Prüfung dauerhaft als n.i.O. (rot), mit Audit der automatischen Entscheidung.',
          'Das Prüfbild wird als n.i.O.-Muster zu Rezept/Kamera gespeichert (Anzahl in Configuration unter Training).',
          'Falsch positiv bleibt die automatische Entscheidung — kein n.i.O.-Muster.',
          'Nachprüfung bleibt offen, ohne die Ampel zu überschreiben.',
        ],
      },
    ],
    related: ['inspection-detail', 'glossary-feedback-verdict', 'faq-feedback-denied'],
  },
  {
    id: 'good-part-training',
    category: 'workflow',
    title: 'Gutteil-Training im Dashboard',
    keywords: [
      'training',
      'gutteil',
      'i.o.',
      'modell',
      'patchcore',
      'memory bank',
      'promoten',
      'aktivieren',
      'historie',
    ],
    summary: 'Nur i.O.-Teile erfassen, trainieren, in der Historie behalten und später wieder aktiv setzen.',
    screen: 'Configuration',
    sections: [
      {
        heading: 'Warum nur Gutteile?',
        paragraphs: [
          'AnomalyMatrix lernt den Sollzustand aus i.O.-Referenzen (Gutteilen). n.i.O.-Teile gehören nicht ins Training.',
          'Ohne echte Memory Bank fällt die Bewertung auf OpenCV-/Hash-Scoring zurück — das sehen Sie unter „Memory Bank“. Die Heatmap ist dann ein Kanten-Residual, kein Modell-Overlay.',
          'Ältere bildweite Banken bleiben ladbar; für eine Patch-Heatmap auf der Defektstelle einmal neu trainieren und promoten.',
        ],
      },
      {
        heading: 'Ablauf in Configuration',
        paragraphs: [
          '1. Rezept wählen und die Kamera in der Kamerauswahl setzen (z. B. USB /dev/video0).',
          '2. Gutteile vor die Kamera legen und „Gutteile erfassen“ — PNG-Dateien landen unter training-images/{Rezept}.',
          '3. „Training starten“ erzeugt einen Kandidaten (Memory-Bank .npz). Vorherige Trainings werden nicht gelöscht.',
          '4. Nach Prüfung „Promoten“ (Validierung) oder „Aktivieren“ (gespeichertes Training wiederverwenden).',
          '5. Bei Bedarf Rollback oder ein älteres Training aus der Historie erneut aktivieren.',
          '6. Prüfung starten → QA „Anomalie bestätigt“ setzt n.i.O. und speichert n.i.O.-Muster (Zähler in diesem Panel).',
        ],
      },
      {
        heading: 'Berechtigungen',
        paragraphs: [
          'Trainieren, erfassen, promoten und aktivieren: Prozessingenieur und Admin (Rechte models.train / models.promote).',
          'Operatoren dürfen den Verlauf und den aktiven Modellstatus lesen, die Aktionen sind deaktiviert.',
        ],
      },
    ],
    related: ['configuration-overview', 'roles-overview', 'what-is-anomalymatrix'],
  },
  {
    id: 'engineer-trends-flow',
    category: 'workflow',
    title: 'Prozessingenieur: Trends interpretieren',
    keywords: ['ingenieur', 'drift', 'prozess', 'trend', 'analyse'],
    summary: 'Frühwarnung bei Prozessdrift erkennen.',
    sections: [
      {
        heading: 'Vorgehen',
        paragraphs: [
          'Trends-Seite öffnen und Average score sowie Anomaly count vergleichen.',
          'Steigt der Durchschnitt über mehrere Stunden/Schichten, Prozessparameter prüfen.',
          'Einzelne Spitzen können Zufall sein — Muster über Zeit bewerten.',
        ],
      },
      {
        heading: 'Abstimmung',
        paragraphs: [
          'Bei anhaltendem Trend: mit Operator und QA Feedback-Historie abstimmen.',
          'Rezept- und Modellversion unter Configuration gegenprüfen.',
        ],
      },
    ],
    related: ['trends-overview', 'glossary-anomaly-score'],
  },
  {
    id: 'plc-opcua-signals',
    category: 'workflow',
    title: 'SPS-Anbindung über OPC UA',
    keywords: ['sps', 'plc', 'opc', 'stop', 'trigger', 'automatisch'],
    summary: 'Automatische Inspektion auslösen und bei rot die Linie stoppen.',
    sections: [
      {
        heading: 'Automatische Inspektion (SPS → Software)',
        paragraphs: [
          'Die SPS setzt ExternalTrigger oder StartRequest auf TRUE (Flanke).',
          'AnomalyMatrix startet dann automatisch eine Prüfung.',
          'Optional: Kamera und Rezept über Request.CameraId / Request.RecipeId vorgeben.',
          'Alternativ: OPC-UA-Methode StartInspection aufrufen.',
        ],
      },
      {
        heading: 'Signale bei rot (Software → SPS)',
        paragraphs: [
          'StopLineRequest = TRUE — Signal zum Anhalten der Linie.',
          'RejectPart = TRUE — Signal zum Ausschleusen des Teils.',
          'DecisionCode = 2 (rot), PassFailBool = FALSE.',
          'ResultReady = TRUE, wenn das Ergebnis vollständig ist.',
        ],
      },
      {
        heading: 'Quittierung Stop',
        paragraphs: [
          'Nach dem Stop setzt die SPS AcknowledgeStop auf TRUE.',
          'AnomalyMatrix löscht StopLineRequest und RejectPart.',
        ],
      },
      {
        heading: 'Bei grün oder gelb',
        paragraphs: [
          'StopLineRequest und RejectPart bleiben FALSE.',
          'DecisionCode: 0 = grün, 1 = gelb.',
        ],
      },
    ],
    related: ['dashboard-kpis', 'decision-colors', 'operator-daily-flow'],
  },
  {
    id: 'dashboard-overview',
    category: 'screens',
    title: 'Dashboard',
    keywords: ['dashboard', 'pipeline', 'inspektion', 'liste', 'kpi'],
    summary: 'Startpunkt für Prüfungen und Übersicht der letzten Ergebnisse.',
    screen: 'Dashboard',
    sections: [
      {
        heading: 'Kopfbereich',
        paragraphs: [
          'Zeigt Linie, aktives Rezept und Modellversion.',
          'Status-Badge: Gesamtzustand der Prüfstation (z. B. bereit / Warnung).',
        ],
      },
      {
        heading: 'Run Inspection Pipeline',
        paragraphs: [
          'Startet eine vollständige Prüfung (Aufnahme, Auswertung, Speicherung).',
          'Während der Laufzeit: Button zeigt „Running…“ — nicht erneut klicken.',
          'Danach Meldung mit Ergebnis (z. B. abgeschlossen mit GREEN/AMBER/RED).',
          '„Open Inspection Detail“ springt zur Detailansicht der ausgewählten Prüfung.',
        ],
      },
      {
        heading: 'Latest inspections',
        paragraphs: [
          'Chronologische Liste: Uhrzeit, Prüf-ID, Teil/Rezept, Ampel-Entscheidung.',
          'Klick auf eine Zeile → Inspection Detail für genau diese Prüfung.',
        ],
      },
    ],
    related: ['dashboard-kpis', 'decision-colors', 'pipeline-messages'],
  },
  {
    id: 'dashboard-kpis',
    category: 'decisions',
    title: 'KPIs auf dem Dashboard',
    keywords: ['kpi', 'cycle', 'anomalie rate', 'queue', 'opc'],
    summary: 'Was die Kennzahlen für den Betrieb bedeuten.',
    sections: [
      {
        heading: 'Cycle p95',
        paragraphs: [
          '95 %-Perzentil der Prüfzykluszeit in Millisekunden.',
          'Steigt der Wert deutlich, kann die Anlage langsamer reagieren — IT/ Instandhaltung informieren.',
        ],
      },
      {
        heading: 'Anomaly Rate',
        paragraphs: [
          'Anteil der letzten Prüfungen mit amber oder rot.',
          'Hohe Rate: Prozess oder Modell genauer beobachten (Trends-Seite).',
        ],
      },
      {
        heading: 'Queue Lag',
        paragraphs: [
          'Wartezeit in der Verarbeitungsqueue.',
          'Hohe Werte können auf Auslastung oder Störung hinweisen.',
        ],
      },
      {
        heading: 'OPC UA Error',
        paragraphs: [
          'Fehlerrate bei der Übertragung des Prüfergebnisses an die Maschinensteuerung.',
          'Nicht null: Ergebnis ggf. nicht an SPS angekommen — Instandhaltung prüfen lassen.',
        ],
      },
    ],
    related: ['dashboard-overview', 'trends-overview'],
  },
  {
    id: 'inspection-detail',
    category: 'screens',
    title: 'Inspection Detail',
    keywords: ['detail', 'score', 'heatmap', 'pass', 'fail', 'review'],
    summary: 'Einzelne Prüfung im Detail ansehen.',
    screen: 'Inspection Detail',
    sections: [
      {
        heading: 'Anzeige',
        paragraphs: [
          'Prüf-ID, Teil/Rezept und Zeitpunkt der Prüfung.',
          'Anomaly score — numerischer Verdachtsindex (0 bis 1, siehe Glossar).',
          'Defect label — vom System vorgeschlagene Fehlerklasse oder „none“.',
          'Pass / Review / Fail — Kurzentscheidung als i.O. / Nachprüfung / n.i.O.',
          'Modellversion und ob eine trainierte Memory Bank geladen ist.',
        ],
      },
      {
        heading: 'Heatmap',
        paragraphs: [
          'Zeigt die Anomalie-Intensität des aktiven Modells auf dem Prüfbild. Hotspots sind Patch-Abstände zur trainierten Memory Bank. Ohne Bank ist die Überlagerung ein Kanten-Residual und als Nicht-Modell gekennzeichnet.',
          'Bildweite (ältere) Banken erzeugen weiterhin ein Modell-Residual zum nächsten Gutteil-Embedding; für Patch-Lokalisierung neu trainieren.',
          'Zur endgültigen Beurteilung immer Teil und Bild vergleichen.',
        ],
      },
      {
        heading: 'Keine Prüfung gewählt?',
        paragraphs: [
          'Zuerst im Dashboard prüfen starten oder eine Zeile unter „Latest inspections“ wählen.',
        ],
      },
    ],
    related: ['qa-review-flow', 'glossary-anomaly-score', 'faq-no-inspection'],
  },
  {
    id: 'trends-overview',
    category: 'screens',
    title: 'Trends',
    keywords: ['trends', 'durchschnitt', 'verlauf', 'samples'],
    summary: 'Verlauf und Kennzahlen mehrerer Prüfungen.',
    screen: 'Trends',
    sections: [
      {
        heading: 'Kennzahlen',
        paragraphs: [
          'Average score — mittlerer Anomalie-Score im betrachteten Zeitraum.',
          'Worst score — höchster Score (schlechtestes Einzelergebnis).',
          'Anomaly count — Anzahl auffälliger Prüfungen (rot).',
          'Total samples — Anzahl ausgewerteter Prüfungen in der Statistik.',
        ],
      },
      {
        heading: 'Latest trend points',
        paragraphs: [
          'Liste der letzten Einzelwerte mit Uhrzeit, ID, Score und Entscheidung.',
          'Quelle wird angezeigt (Live-Statistik oder lokale Liste).',
        ],
      },
      {
        heading: 'Ampel neben dem Durchschnitt',
        paragraphs: [
          'Leitet sich aus dem Average score ab — gleiche Schwellen wie bei Einzelprüfungen.',
        ],
      },
    ],
    related: ['engineer-trends-flow', 'decision-colors'],
  },
  {
    id: 'configuration-overview',
    category: 'screens',
    title: 'Configuration',
    keywords: ['config', 'rezept', 'modell', 'lizenz', 'profil'],
    summary: 'Welche Einstellungen und Statuswerte Sie hier sehen.',
    screen: 'Configuration',
    sections: [
      {
        heading: 'Rezept & Modell',
        paragraphs: [
          'Recipe version — aktives Prüfrezept (Beleuchtung, Kamera, Grenzen).',
          'Model profile — welches Anomalie-Modell ausgewertet wird.',
          'Training / Modelle — Gutteil-Bilder erfassen, PatchCore trainieren, Kandidaten promoten und ältere Trainings wieder aktiv setzen.',
          'Entscheidungsschwellen — Empfindlichkeit i.O. / Nachprüfung / n.i.O. je Rezept (Prozessingenieur/Admin).',
          'EOL-Stationsstandard / Vision Setup — Kamerarollen (oben/seitlich/unten/STF), Objektiv-/FOV-Notizen, Belichtung und Checkliste. Vorlage JSON/YAML exportieren oder für eine andere Linie klonen.',
          'Speicher & Retention — Objektzahl, TTL, Archiv, Watchdog für 24h-Betrieb. EPC der letzten Prüfung steht im Dashboard.',
          'n.i.O.-Muster — Anzahl der von QA bestätigten Defektbilder (nicht ins Gutteil-Training gemischt).',
          'Nur Prozessingenieur oder Admin dürfen trainieren; Operatoren sehen den Verlauf lesend.',
        ],
      },
      {
        heading: 'Integration',
        paragraphs: [
          'OPC UA profile — wie Ergebnisse an die Anlage gemeldet werden. MQTT-Trigger (SPS/MES) läuft zusätzlich; beide dürfen parallel aktiv sein.',
          'Audit mode — ob Prüf- und Feedback-Aktionen protokolliert werden.',
        ],
      },
      {
        heading: 'Lizenz',
        paragraphs: [
          'License tier — gebuchte Stufe.',
          'License active — darf die Software prüfen (bei „false“ IT informieren).',
          'Grace active — vorübergehende Toleranz ohne Live-Lizenzserver.',
          'Lizenz & Abrechnung — Administratoren kaufen, verlängern oder kündigen hier über Stripe. Nicht die Vendor-Admin-Oberfläche nutzen.',
        ],
      },
    ],
    related: ['license-status-user', 'roles-overview', 'good-part-training', 'eol-vision-setup'],
  },
  {
    id: 'eol-vision-setup',
    category: 'screens',
    title: 'EOL-Stationsstandard (Vision Setup)',
    keywords: ['vision', 'eol', 'kamera', 'unten', 'epc', 'mqtt', 'retention', 'checkliste', 'basler'],
    summary: 'Kamerarollen, Optik-Notizen, Checkliste und Vorlage für andere Linien.',
    screen: 'Configuration',
    sections: [
      {
        heading: 'Was Sie eintragen',
        paragraphs: [
          'Pro Slot: Rolle (oben, seitlich, unten, STF, Vollständigkeit), Objektiv-/FOV-Notizen, Belichtung, Gain, Trigger und optionale Lichtsteuerung.',
          'Die Perspektiv-Checkliste (Ecken, Kanten, Merkmale, Unteransicht) bestätigt der Operator vor Go-Live.',
          'JSON/YAML exportieren oder das Profil auf eine neue Stations-ID klonen — das ist der rollenfähige Standard für Phase 3.',
        ],
      },
      {
        heading: 'EPC und Trigger',
        paragraphs: [
          'Jedes Capture hängt an einer EPC (oder Prozess-ID) — sichtbar im Dashboard und Inspektionsdetail.',
          'Die SPS kann per OPC UA oder MQTT auslösen; beides darf parallel laufen.',
        ],
      },
    ],
    related: ['configuration-overview', 'operator-daily-flow'],
  },
  {
    id: 'license-status-user',
    category: 'screens',
    title: 'Lizenzstatus verstehen',
    keywords: ['lizenz', 'licensed', 'grace', 'aktiv', 'abrechnung', 'billing', 'stripe', 'checkout'],
    summary: 'Was die Lizenzanzeige auf Configuration für Sie bedeutet.',
    sections: [
      {
        heading: 'Licensed (aktiv)',
        paragraphs: ['Prüfungen sind freigegeben. Keine Aktion nötig.'],
      },
      {
        heading: 'Unlicensed / nicht aktiv',
        paragraphs: [
          'Neue Prüfungen können blockiert sein.',
          'Schichtleitung oder IT informieren — nicht selbst am System konfigurieren.',
        ],
      },
      {
        heading: 'Grace active',
        paragraphs: [
          'Kurzfristiger Übergangsmodus (z. B. Netzwerkausfall zum Lizenzserver).',
          'Betrieb möglich, aber IT sollte den Zustand zeitnah klären.',
        ],
      },
    ],
    related: ['configuration-overview', 'faq-license-blocked'],
  },
  {
    id: 'roles-overview',
    category: 'roles',
    title: 'Rollen — wer darf was?',
    keywords: ['rolle', 'operator', 'qa', 'admin', 'berechtigung'],
    summary: 'Übersicht der Benutzerrollen in der Oberfläche.',
    sections: [
      {
        heading: 'Operator',
        paragraphs: [
          'Prüfungen starten und Ergebnisse ansehen.',
          'Dashboard, Detail (ohne Feedback), Trends und Configuration lesen.',
        ],
      },
      {
        heading: 'QA Lead',
        paragraphs: [
          'Alles wie Operator, plus QA-Feedback auf Inspection Detail.',
          'Bewertungen für Qualitätssicherung und Modellverbesserung.',
        ],
      },
      {
        heading: 'Process Engineer',
        paragraphs: [
          'Auswertung von Trends, Rezepten und Modellen.',
          'In Configuration: Gutteile erfassen, Modelle trainieren, promoten und ältere Trainings wieder aktivieren.',
          'Feedback lesen; typischerweise keine neuen Prüfungen am Band.',
        ],
      },
      {
        heading: 'Administrator',
        paragraphs: [
          'Vollzugriff inkl. Audit und Systemthemen.',
          'Richtet Rollen und Lizenzen ein — nicht Aufgabe des Operators am Band.',
        ],
      },
    ],
    related: ['qa-review-flow', 'faq-feedback-denied'],
  },
  {
    id: 'decision-colors',
    category: 'decisions',
    title: 'Ampelfarben: i.O., Nachprüfung, n.i.O.',
    keywords: ['grün', 'amber', 'rot', 'green', 'red', 'i.o.', 'n.i.o.', 'pass', 'fail'],
    summary: 'Bedeutung von i.O. (grün), Nachprüfung (gelb) und n.i.O. (rot).',
    sections: [
      {
        heading: 'Grün — i.O.',
        paragraphs: [
          'Kein relevanter Anomalie-Verdacht. Teil ist i.O.',
          'Weiterproduktion nach Werksstandard.',
        ],
      },
      {
        heading: 'Gelb — Nachprüfung',
        paragraphs: [
          'Grenzbereich — menschliche Nachprüfung empfohlen.',
          'Nicht automatisch ausschleusen; QA-Regelwerk beachten.',
        ],
      },
      {
        heading: 'Rot — n.i.O.',
        paragraphs: [
          'Starker Anomalie-Verdacht, Fehlerklasse oder QA-Bestätigung.',
          'Teil sperren/nacharbeiten gemäß Prozess; QA einbinden.',
        ],
      },
      {
        heading: 'Schwellen in der HMI',
        paragraphs: [
          'Standard: Nachprüfung ab 0,55, n.i.O. ab 0,85. Prozessingenieur/Admin stellen die Werte unter Configuration je Rezept ein.',
          'QA „Anomalie bestätigt“ überschreibt die Anzeige auf n.i.O., unabhängig vom Score.',
        ],
      },
    ],
    related: ['glossary-anomaly-score', 'operator-daily-flow'],
  },
  {
    id: 'pipeline-messages',
    category: 'faq',
    title: 'Meldungen bei „Run Inspection Pipeline“',
    keywords: ['pipeline', 'running', 'fehlgeschlagen', 'meldung', 'status'],
    summary: 'Was die Statusmeldungen nach dem Prüfstart bedeuten.',
    sections: [
      {
        heading: '„Pipeline wird ausgeführt …“',
        paragraphs: ['Prüfung läuft — warten bis Erfolg oder Fehler angezeigt wird.'],
      },
      {
        heading: '„Inspektion … abgeschlossen (GREEN/AMBER/RED)“',
        paragraphs: ['Prüfung erfolgreich. Ergebnis steht in der Liste und in Inspection Detail.'],
      },
      {
        heading: '„Pipeline fehlgeschlagen …“',
        paragraphs: [
          'Prüfung konnte nicht abgeschlossen werden.',
          'Verbindungsstatus oben prüfen; erneut versuchen.',
          'Bleibt der Fehler: Schichtleitung oder IT — nicht mehrfach ohne Rücksprache klicken.',
        ],
      },
    ],
    related: ['faq-connection-offline', 'dashboard-overview'],
  },
  {
    id: 'faq-no-inspection',
    category: 'faq',
    title: '„No inspection selected“',
    keywords: ['keine', 'ausgewählt', 'leer', 'detail'],
    summary: 'Inspection Detail ohne gewählte Prüfung.',
    sections: [
      {
        heading: 'Lösung',
        paragraphs: [
          'Zum Dashboard wechseln.',
          '„Run Inspection Pipeline“ ausführen oder in „Latest inspections“ eine Zeile anklicken.',
          'Dann erneut Inspection Detail öffnen.',
        ],
      },
    ],
    related: ['inspection-detail', 'operator-daily-flow'],
  },
  {
    id: 'faq-feedback-denied',
    category: 'faq',
    title: 'Feedback lässt sich nicht senden',
    keywords: ['feedback', 'fehlgeschlagen', 'berechtigung', '403'],
    summary: 'Fehlermeldung beim QA-Feedback.',
    sections: [
      {
        heading: 'Typische Ursache',
        paragraphs: [
          'Ihr Benutzer hat die QA-Rolle nicht (nur Operator oder Ingenieur ohne Feedback-Recht).',
        ],
      },
      {
        heading: 'Was tun?',
        paragraphs: [
          'QA Lead oder Administrator bittet, das Feedback einzutragen.',
          'Für dauerhaften Zugriff: Administrator um Zuweisung der Rolle „QA Lead“ bitten.',
        ],
      },
    ],
    related: ['qa-review-flow', 'roles-overview'],
  },
  {
    id: 'faq-connection-offline',
    category: 'faq',
    title: '„Offline-Seed-Daten“ in der Kopfzeile',
    keywords: ['offline', 'verbunden', 'backend', 'verbindung'],
    summary: 'Die Oberfläche zeigt keine Live-Verbindung.',
    sections: [
      {
        heading: 'Bedeutung',
        paragraphs: [
          'Die Anzeige arbeitet mit Ersatz-/Demo-Daten.',
          'Neue Prüfungen sind unter Umständen nicht möglich oder nicht persistent.',
        ],
      },
      {
        heading: 'Was tun?',
        paragraphs: [
          'Keine produktionskritischen Entscheidungen allein auf Basis der Anzeige treffen.',
          'IT oder Instandhaltung informieren — Verbindung zur Prüfungssoftware wiederherstellen lassen.',
        ],
      },
    ],
    related: ['pipeline-messages', 'hmi-overview'],
  },
  {
    id: 'faq-license-blocked',
    category: 'faq',
    title: 'Prüfung startet nicht (Lizenz)',
    keywords: ['lizenz', 'blockiert', 'prüfung', 'gesperrt'],
    summary: 'Prüfbutton liefert Fehler wegen Lizenz.',
    sections: [
      {
        heading: 'Anzeichen',
        paragraphs: [
          'Configuration zeigt License active: false.',
          'Pipeline-Meldung deutet auf gesperrte Funktion hin.',
        ],
      },
      {
        heading: 'Was tun?',
        paragraphs: [
          'Schichtleitung und IT informieren.',
          'Ein Administrator kann die Lizenz unter Konfiguration → Lizenz & Abrechnung kaufen oder verlängern (Stripe-Checkout in AnomalyMatrix).',
        ],
      },
    ],
    related: ['license-status-user', 'configuration-overview'],
  },
  {
    id: 'glossary-anomaly-score',
    category: 'glossary',
    title: 'Anomalie-Score',
    keywords: ['score', 'wert', 'zahl', 'schwellwert'],
    summary: 'Numerischer Verdachtsindex von 0 bis 1.',
    sections: [
      {
        heading: 'Einordnung',
        paragraphs: [
          'Je höher der Wert, desto stärker weicht das Teil vom „Gut-Teil“-Modell ab.',
          'Ab dem Rezept-Schwellenwert (Standard 0,55): Nachprüfung (gelb). Ab n.i.O.-Schwelle (Standard 0,85): n.i.O. (rot). Darunter: i.O. (grün).',
          'Schwellen stellt der Prozessingenieur in Configuration ein — die Ampelentscheidung ist maßgeblich.',
        ],
      },
    ],
    related: ['decision-colors', 'trends-overview'],
  },
  {
    id: 'glossary-inspection',
    category: 'glossary',
    title: 'Inspektion (Prüfung)',
    keywords: ['inspection', 'prüfung', 'zyklus', 'lauf'],
    summary: 'Ein kompletter automatischer Prüfdurchlauf.',
    sections: [
      {
        heading: 'Ablauf',
        paragraphs: [
          'Bild aufnehmen → Software wertet aus → Entscheidung (grün/amber/rot) → Speicherung.',
          'Ergebnis kann an die Maschinensteuerung gemeldet werden.',
        ],
      },
    ],
    related: ['dashboard-overview', 'operator-daily-flow'],
  },
  {
    id: 'glossary-feedback-verdict',
    category: 'glossary',
    title: 'Feedback-Verdicts',
    keywords: ['bestätigen', 'falsch positiv', 'nachprüfung', 'verdict'],
    summary: 'Ihre QA-Einstufung nach der Prüfung.',
    sections: [
      {
        heading: 'Anomalie bestätigen',
        paragraphs: [
          'Das System hat recht — echter Defekt. Die Prüfung wird als n.i.O. angezeigt und das Bild als n.i.O.-Muster gespeichert.',
        ],
      },
      {
        heading: 'Falsch positiv',
        paragraphs: ['Das Teil ist in Ordnung — die Software hat fälschlich alarmiert.'],
      },
      {
        heading: 'Nachprüfung nötig',
        paragraphs: ['Noch unklar — weitere Analyse durch QA oder Labor erforderlich.'],
      },
    ],
    related: ['qa-review-flow', 'inspection-detail'],
  },
  {
    id: 'glossary-recipe',
    category: 'glossary',
    title: 'Rezept (Recipe)',
    keywords: ['rezept', 'recipe', 'version', 'kamera'],
    summary: 'Prüfvorschrift für ein Teil am aktuellen Platz.',
    sections: [
      {
        heading: 'Enthält typischerweise',
        paragraphs: [
          'Kamera- und Beleuchtungseinstellungen.',
          'Zugeordnetes Anomalie-Modell und Grenzwerte.',
          'Wird zentral gepflegt — unter Configuration nur einsehbar.',
        ],
      },
    ],
    related: ['configuration-overview'],
  },
];

export function getArticlesByCategory(categoryId) {
  return HELP_ARTICLES.filter((a) => a.category === categoryId);
}
