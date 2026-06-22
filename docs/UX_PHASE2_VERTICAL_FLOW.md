# UX Phase 2 Vertical Flow (MVP)

> **Implementiert (v0.6.0):** Dashboard → Run → Recent → Detail; Trends aus API; Feedback auf Detail-Seite.

## Ziel
Durchgängiger Operator-Pfad von Dashboard-Aktion bis Detail-/Trend-Sicht.

## Vertical path
1. Dashboard: `Run Inspection Pipeline`
2. Ergebnis landet in `Latest inspections`
3. Klick auf Inspection → `Inspection Detail`
4. Trends-Seite zeigt aggregierte Werte aus neuesten Inspektionen

## State clarity
- Run button state: `idle / running / success / error`
- Inspection labels: `green / amber / red`
- Detail decision labels: `Pass / Review / Fail`

## Operator guidance
- Bei Backend-Fehler zeigt Dashboard klare Fehlermeldung.
- Fallback lädt `recent inspections`, damit HMI bedienbar bleibt.
