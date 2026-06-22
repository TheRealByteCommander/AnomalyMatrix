# edge-acquisition

HTTP Capture-Service für AnomalyMatrix (MVP-Stub).

## Funktion
- `POST /capture` — synthetischer Frame + Metadaten (Kamera, Recipe, Timestamp)
- Wird von der API über `EDGE_ACQUISITION_URL` angesprochen

## Port
**8091** (Docker Compose: `edge-acquisition:8091`)

## Lokal starten
```bash
pip install -r requirements.txt
uvicorn service:app --host 0.0.0.0 --port 8091
```

Backend `.env`: `EDGE_ACQUISITION_URL=http://127.0.0.1:8091`

## Folgerelease
Echte Kamera-/Beleuchtungsanbindung (GigE, GenICam, Trigger-Sync).
