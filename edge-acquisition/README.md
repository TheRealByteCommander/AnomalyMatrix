# edge-acquisition

HTTP Capture-Service für AnomalyMatrix.

## Funktion
- `GET /cameras` — Hardware-Erkennung (V4L2/OpenCV) bzw. Synthetic-Kameras
- `POST /capture` — Frame + Metadaten (`camera_id`, optional `source`)
- Wird von der API über `EDGE_ACQUISITION_URL` angesprochen

## Multi-Kamera
Bis zu 4 Geräte. Mapping optional über `CAMERA_SOURCES_JSON`.  
Auswahl und Same-Case-Aggregation liegen in der API (`/api/v1/cameras*`, Inspektion).

## Port
**8091** (Docker Compose: `edge-acquisition:8091`)

## Lokal starten
```bash
pip install -r requirements.txt
uvicorn service:app --host 0.0.0.0 --port 8091
```

Backend `.env`: `EDGE_ACQUISITION_URL=http://127.0.0.1:8091`

## Folgerelease
GigE, GenICam, Trigger-Sync.
