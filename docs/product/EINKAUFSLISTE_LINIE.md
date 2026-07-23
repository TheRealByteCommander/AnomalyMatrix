# Einkaufsliste — AnomalyMatrix Linien-Setup (Line Connect)

Stand: **v1.1.0** · Ziel: **eine Prüfstelle** mit Kamera, Edge-IPC, Operator-HMI und **OPC-UA-SPS-Anbindung**

> Keine Markenbindung. Angaben sind **Produktklassen** für Einkauf / Ausschreibung.  
> Software-Kamerapfad heute: **OpenCV / V4L2 (USB)**. GigE/GenICam: Folgerelease — siehe Hinweise.

Verwandte Docs: [`ANOMALYMATRIX_ADDON_SETS_VERTIEB.md`](./ANOMALYMATRIX_ADDON_SETS_VERTIEB.md) · [`../INSTALLATION.md`](../INSTALLATION.md) · [`../CONFIGURATION.md`](../CONFIGURATION.md)

---

## Kurzüberblick (1 Prüfstelle)

| Bereich | Stück | Zweck |
|---------|------:|-------|
| Industrie-PC (Host) | 1 | AnomalyMatrix-Stack (Docker) |
| USB-Industriekamera + Objektiv | 1 | Bilderfassung (V4L2) |
| LED-Beleuchtung | 1 Set | stabile Bildqualität |
| Mechanik / Halterung | 1 Set | feste Prüfposition |
| Operator-Panel / Monitor | 1 | HMI-Ampel am Band |
| OT-Netzwerk | 1 Set | IPC ↔ SPS ↔ optional Office |
| OPC-UA-fähige SPS / Bridge | 1* | Trigger / Stop / Reject |

\* Oft **vorhanden** an der Linie — dann nur Freischaltung OPC UA + Mapping.

**Richtbudget Hardware (ohne SPS, ohne Montagearbeit):** typisch **3.500–9.000 €** je nach IPC-/Kamera-Klasse.  
Software-Lizenz, Inbetriebnahme und SPS-Workshop separat.

---

## 1. Rechner & Betriebssystem

| Pos. | Menge | Artikel | Spezifikation (Minimum / empfohlen) | Hinweis |
|------|------:|---------|-------------------------------------|---------|
| 1.1 | 1 | Fanless Industrie-PC (IPC) | **x86_64**, **8 Kerne**, **16–32 GB RAM**, **256–512 GB SSD** | Pilot-Minimum laut Install: 4 Kerne / 8 GB / 40 GB — Linie: höher planen |
| 1.2 | 1 | OS-Installation | **Ubuntu Server 24.04 LTS** | kein Desktop nötig; Browser nur für HMI |
| 1.3 | 1–2 | Gigabit-Ethernet | 2× NIC ideal (OT + Office/Admin) | Ports: 80/443 HMI, 4840 OPC-UA, 22 SSH |
| 1.4 | 1 | DIN-Schienen-Netzteil | 24 V DC, Leistung nach IPC+Kamera+Licht | oder IPC mit integriertem PSU |
| 1.5 | 1 | USV (optional) | 500–1000 VA, reine Sinus | sauberes Herunterfahren bei Spannungsabfall |

**Nicht nötig:** dedizierte GPU (Inferenz aktuell OpenCV-CPU).

---

## 2. Kamera & Optik (softwareseitig unterstützt)

| Pos. | Menge | Artikel | Spezifikation | Hinweis |
|------|------:|---------|---------------|---------|
| 2.1 | 1 | **USB3 / UVC-Industriekamera** | Global Shutter bevorzugt, ≥ **2 MP**, V4L2-fähig, fester USB3-Anschluss | Host-Gerät: `/dev/video0` via `docker-compose.camera.yml` |
| 2.2 | 1 | Objektiv | C-/CS-Mount, Brennweite nach Sichtfeld & Arbeitsabstand | erst FOV/Abstand messen, dann kaufen |
| 2.3 | 1 | Filter (optional) | IR-Cut / Bandpass je nach Licht | reduziert Blendung / Drift |
| 2.4 | 1 | USB3-Kabel industriell | geschirmt, verriegelt, Länge ≤ 3–5 m | aktive Repeater nur wenn nötig |
| 2.5 | 1 | Kamerahalterung | schwingungsarm, justierbar (X/Y/Z/Winkel) | nach Erstsetup fest arretieren |

### Bewusst nicht in v1.1.0 einkaufen (ohne Integrationsprojekt)

| Artikel | Status |
|---------|--------|
| GigE Vision / GenICam (Basler, IDS, …) + PoE-Switch | **Noch kein Treiberpfad** in AnomalyMatrix — Folgerelease |
| Framegrabber / Camera Link | nicht vorgesehen |

> Für Linien: **industrielle USB3-Kamera mit V4L2** wählen (viele Hersteller liefern Linux-UVC oder V4L2-Treiber). Vor Kauf: Gerät unter Ubuntu als `/dev/video0` verifizieren.

---

## 3. Beleuchtung

| Pos. | Menge | Artikel | Spezifikation | Hinweis |
|------|------:|---------|---------------|---------|
| 3.1 | 1 | LED-Ring- oder Balkenlicht | konstantstrom, dimmbar, Farbtemperatur stabil (z. B. 5000–6500 K) | diffuse Beleuchtung für matte Oberflächen |
| 3.2 | 1 | Netzteil / Controller | passend zur LED (24 V typisch) | getrennt schaltbar vom IPC |
| 3.3 | 0–1 | Diffusor / Abschirmung | Streuscheibe, Lichtschutz | gegen Hallenlicht / Reflexe |
| 3.4 | 0–1 | Dunkelfeld / seitliches Licht | bei Kratzern / Kanten | applikationsabhängig |

Ohne stabile Beleuchtung sind Score und Ampel **nicht linienfähig**.

---

## 4. Mechanik Prüfstelle

| Pos. | Menge | Artikel | Spezifikation | Hinweis |
|------|------:|---------|---------------|---------|
| 4.1 | 1 | Prüfhalter / Nest | wiederholgenaue Lage des Teils | Kundenteil-spezifisch |
| 4.2 | 1 | Gestell / Profilsystem | Aluminium-Profil, Boden/Maschinenmontage | Schwingungen vermeiden |
| 4.3 | 1 | Schutz (optional) | Schutzscheibe, Gehäuse IP54+ | Schmutz, Öl, Reinigung |
| 4.4 | 1 | Sensor „Teil im Prüffeld“ | Initator / Lichtschranke → **SPS** | Trigger kommt von der SPS, nicht von der Software |

---

## 5. Operator-HMI

| Pos. | Menge | Artikel | Spezifikation | Hinweis |
|------|------:|---------|---------------|---------|
| 5.1 | 1 | Industrie-Monitor oder Panel-PC | **≥ 15″**, Full-HD, optional Touch | Browser auf `https://<HOST>/` |
| 5.2 | 1 | Halterung / Schwenkarm | ergonomisch am Band | Ampel muss ohne Zoom lesbar sein |
| 5.3 | 1 | Tastatur + Maus (Setup) | industriell oder abdeckbar | Admin/QA; Operator oft Touch-only |

Kein separates Thin-Client nötig, wenn Panel-PC den Browser lokal öffnet **oder** Monitor am IPC hängt.

---

## 6. Netzwerk & OT-Sicherheit

| Pos. | Menge | Artikel | Spezifikation | Hinweis |
|------|------:|---------|---------------|---------|
| 6.1 | 1 | Managed Switch (OT) | Gigabit, VLANs möglich | IPC, SPS, Panel |
| 6.2 | Set | Patchkabel Cat6 | industriell, geschirmt | feste Verlegung |
| 6.3 | 1 | Firewall / Router-Regel | Freigaben siehe unten | oft IT/OT vorhanden |
| 6.4 | 1 | TLS-Zertifikat | Kunden-PKI oder intern | Compose-TLS-Overlay / Caddy |

### Ports (Host)

| Port | Dienst |
|------|--------|
| 22 | SSH (Admin) |
| 80 / 443 | HMI |
| 4840 | OPC-UA Gateway ↔ SPS |

Edge, Postgres, MinIO, Influx: **nur Docker-Netz** (keine Host-Ports nötig).

---

## 7. SPS / Automatisierung (Line Connect)

| Pos. | Menge | Artikel | Spezifikation | Hinweis |
|------|------:|---------|---------------|---------|
| 7.1 | 1* | SPS mit **OPC UA Server oder Client** | Siemens, Beckhoff, Rockwell, … | *meist vorhanden |
| 7.2 | 0–1 | OPC-UA-Bridge / Gateway-HW | falls SPS kein natives OPC UA | alternativ Soft-Bridge |
| 7.3 | — | Kunden-Zertifikate | Server/Client-PEMs für Sign/Encrypt | Mount nach `opcua_certs` |
| 7.4 | — | SPS-Engineering-Zeit | Trigger, Stop, Reject, Acknowledge | NodeSet: `contracts/opcua_nodeset_mapping_v1.json` |

### Signale (Software-seitig vorgesehen)

| Richtung | Beispiele |
|----------|-----------|
| SPS → AMX | `ExternalTrigger` / `StartInspection`, Rezept/Kamera-ID |
| AMX → SPS | Ampel/Score, `StopLineRequest`, `RejectPart` |
| Operator/SPS | `AcknowledgeStop` |

---

## 8. Verbrauch / Betrieb (Erstausstattung)

| Pos. | Menge | Artikel | Hinweis |
|------|------:|---------|---------|
| 8.1 | 1 | Satz Gut-Teile zur Kalibrierung | Rezept / Baseline |
| 8.2 | 1 | Satz typischer Defektteile (falls verfügbar) | Schwellwert-Abstimmung |
| 8.3 | 1 | Backup-Medium / NAS-Ziel | `scripts/backup/` |
| 8.4 | 1 | CREDENTIALS-/Secret-Aufbewahrung | Tresor / Passwortmanager (nicht im Klartext am Schrank) |

---

## 9. Was der Kunde oft schon hat (nicht doppelt kaufen)

- [ ] OPC-UA-fähige Linien-SPS  
- [ ] OT-Switch / Firewall  
- [ ] 24-V-Versorgung am Schaltschrank  
- [ ] Panel-PC am Band (Browser reicht)  
- [ ] Mechanische Prüffläche / Nest  

---

## 10. Empfohlene Kaufreihenfolge

1. **IPC + Ubuntu 24.04** → Software installieren (`docs/INSTALLATION.md`)  
2. **Kamera + Licht + Mechanik** → Bildqualität / Rezept  
3. **HMI-Panel** → Operator-Abnahme Ampel  
4. **SPS-Mapping + PKI** → Takt-Trigger & Stop/Reject  
5. **TLS + Backup + Runbook** → Go-Live (`docs/PRODUCTION_RUNBOOK.md`)

---

## 11. Checkliste vor Bestellung

- [ ] Arbeitsabstand und Sichtfeld gemessen → Objektiv gewählt  
- [ ] USB3-Kamera unter Ubuntu als `/dev/video0` bestätigt (Datenblatt / Testgerät)  
- [ ] Hallenlicht / Reflexe geprüft → Beleuchtungskonzept  
- [ ] SPS-OPC-UA-Fähigkeit und Netzwerkfreigabe 4840 geklärt  
- [ ] Speicherplatz für Rohbilder/Heatmaps dimensioniert (SSD ≥ 256 GB)  
- [ ] Keine GigE-only-Kamera bestellt, solange GenICam-Pfad fehlt  

---

## 12. Abgrenzung Software vs. Hardware-Lieferung

| Liefert AnomalyMatrix (Software-Release) | Liefert Einkauf / Integrator |
|------------------------------------------|------------------------------|
| API, HMI, Edge, OPC-UA-Gateway, Installer | IPC, Kamera, Licht, Mechanik, Panel |
| Compose-Overlays (Prod, Camera, TLS) | OT-Netz, Zertifikate, SPS-Programm |
| Docs & NodeSet-Contract | Montage, Schaltschrank, Abnahme |

*Dokumentversion: 1.0 · Juli 2026 · Basis: AnomalyMatrix v1.1.0 / Add-on Set Line Connect*
