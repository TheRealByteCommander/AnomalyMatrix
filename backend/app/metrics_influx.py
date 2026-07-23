from __future__ import annotations

import atexit
import os
import queue
import threading
from datetime import datetime, timezone
from typing import Any


def _influx_enabled() -> bool:
    return bool(os.getenv("INFLUX_URL", "").strip())


_client = None
_client_lock = threading.Lock()
_write_queue: queue.Queue | None = None
_worker: threading.Thread | None = None
_stop = threading.Event()


def _get_client():
    global _client
    if not _influx_enabled():
        return None
    try:
        from influxdb_client import InfluxDBClient
    except ImportError:
        return None

    url = os.getenv("INFLUX_URL", "").strip()
    token = os.getenv("INFLUX_TOKEN", "").strip()
    org = os.getenv("INFLUX_ORG", "anomalymatrix").strip()
    if not url or not token:
        return None

    with _client_lock:
        if _client is None:
            _client = InfluxDBClient(url=url, token=token, org=org)
        return _client


def _ensure_worker() -> None:
    global _write_queue, _worker
    if _write_queue is not None:
        return
    _write_queue = queue.Queue(maxsize=1000)
    _worker = threading.Thread(target=_drain_queue, name="influx-writer", daemon=True)
    _worker.start()


def _drain_queue() -> None:
    assert _write_queue is not None
    org = os.getenv("INFLUX_ORG", "anomalymatrix").strip()
    bucket = os.getenv("INFLUX_BUCKET", "inspection_metrics").strip()
    while not _stop.is_set():
        try:
            point = _write_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            client = _get_client()
            if client is None:
                continue
            write_api = client.write_api()
            write_api.write(bucket=bucket, org=org, record=point)
            write_api.close()
        except Exception:
            pass
        finally:
            _write_queue.task_done()


def _enqueue(point: Any) -> bool:
    if not _influx_enabled():
        return False
    try:
        from influxdb_client import Point  # noqa: F401
    except ImportError:
        return False
    _ensure_worker()
    assert _write_queue is not None
    try:
        _write_queue.put_nowait(point)
        return True
    except queue.Full:
        return False


def _shutdown() -> None:
    _stop.set()
    global _client
    with _client_lock:
        if _client is not None:
            try:
                _client.close()
            except Exception:
                pass
            _client = None


atexit.register(_shutdown)


def record_inspection_metrics(
    *,
    inspection_id: str,
    score: float,
    latency_ms: float,
    decision: str,
    provider: str,
    opcua_published: bool,
) -> bool:
    """Queue one point for async write to Influx (no-op if INFLUX_URL unset)."""
    if not _influx_enabled():
        return False
    try:
        from influxdb_client import Point
    except ImportError:
        return False

    point = (
        Point("inspection_metrics")
        .tag("decision", decision)
        .tag("provider", provider)
        .tag("opcua_published", "true" if opcua_published else "false")
        .tag("inspection_id", inspection_id[:64])
        .field("anomaly_score", float(score))
        .field("latency_ms", float(latency_ms))
        .field("opcua_error", 0.0 if opcua_published else 1.0)
        .time(datetime.now(timezone.utc))
    )
    return _enqueue(point)


def record_process_trend(*, avg_score: float, drift_score: float | None = None) -> bool:
    if not _influx_enabled():
        return False
    try:
        from influxdb_client import Point
    except ImportError:
        return False

    point = (
        Point("process_trends")
        .field("rolling_avg_score", float(avg_score))
        .field("drift_score", float(drift_score if drift_score is not None else avg_score))
        .time(datetime.now(timezone.utc))
    )
    return _enqueue(point)


def query_observability_summary() -> dict:
    """Best-effort KPI summary from Influx; empty dict if unavailable."""
    if not _influx_enabled():
        return {}

    client = _get_client()
    if client is None:
        return {}

    org = os.getenv("INFLUX_ORG", "anomalymatrix").strip()
    bucket = os.getenv("INFLUX_BUCKET", "inspection_metrics").strip()
    # Bucket name is controlled via env (ops), not user input.
    flux = f'''
from(bucket: "{bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "inspection_metrics")
  |> filter(fn: (r) => r._field == "latency_ms" or r._field == "opcua_error")
  |> group(columns: ["_field"])
  |> mean()
'''
    try:
        tables = client.query_api().query(flux, org=org)
        latency_ms = 0.0
        opcua_error_rate = 0.0
        for table in tables:
            for record in table.records:
                if record.get_field() == "latency_ms":
                    latency_ms = float(record.get_value())
                if record.get_field() == "opcua_error":
                    opcua_error_rate = float(record.get_value()) * 100.0
        return {
            "inference_p95_ms": round(latency_ms, 2),
            "opc_ua_publish_error_rate_pct": round(opcua_error_rate, 2),
            "source": "influx",
        }
    except Exception:
        return {}
