from __future__ import annotations

import os
from datetime import datetime, timezone


def _influx_enabled() -> bool:
    return bool(os.getenv("INFLUX_URL", "").strip())


def record_inspection_metrics(
    *,
    inspection_id: str,
    score: float,
    latency_ms: float,
    decision: str,
    provider: str,
    opcua_published: bool,
) -> bool:
    """Write one point to Influx bucket `inspection_metrics` (no-op if INFLUX_URL unset)."""
    if not _influx_enabled():
        return False

    try:
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS
    except ImportError:
        return False

    url = os.getenv("INFLUX_URL", "").strip()
    token = os.getenv("INFLUX_TOKEN", "").strip()
    org = os.getenv("INFLUX_ORG", "anomalymatrix").strip()
    bucket = os.getenv("INFLUX_BUCKET", "inspection_metrics").strip()

    if not url or not token:
        return False

    point = (
        Point("inspection_metrics")
        .tag("decision", decision)
        .tag("provider", provider)
        .tag("opcua_published", "true" if opcua_published else "false")
        .field("anomaly_score", float(score))
        .field("latency_ms", float(latency_ms))
        .field("opcua_error", 0.0 if opcua_published else 1.0)
        .time(datetime.now(timezone.utc))
    )

    try:
        with InfluxDBClient(url=url, token=token, org=org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=bucket, org=org, record=point)
        return True
    except Exception:
        return False


def record_process_trend(*, avg_score: float, drift_score: float | None = None) -> bool:
    if not _influx_enabled():
        return False
    try:
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS
    except ImportError:
        return False

    url = os.getenv("INFLUX_URL", "").strip()
    token = os.getenv("INFLUX_TOKEN", "").strip()
    org = os.getenv("INFLUX_ORG", "anomalymatrix").strip()
    bucket = os.getenv("INFLUX_BUCKET", "inspection_metrics").strip()

    if not url or not token:
        return False

    point = (
        Point("process_trends")
        .field("rolling_avg_score", float(avg_score))
        .field("drift_score", float(drift_score if drift_score is not None else avg_score))
        .time(datetime.now(timezone.utc))
    )
    try:
        with InfluxDBClient(url=url, token=token, org=org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=bucket, org=org, record=point)
        return True
    except Exception:
        return False


def query_observability_summary() -> dict:
    """Best-effort KPI summary from Influx; empty dict if unavailable."""
    if not _influx_enabled():
        return {}

    try:
        from influxdb_client import InfluxDBClient
    except ImportError:
        return {}

    url = os.getenv("INFLUX_URL", "").strip()
    token = os.getenv("INFLUX_TOKEN", "").strip()
    org = os.getenv("INFLUX_ORG", "anomalymatrix").strip()
    bucket = os.getenv("INFLUX_BUCKET", "inspection_metrics").strip()
    if not url or not token:
        return {}

    flux = f'''
from(bucket: "{bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "inspection_metrics")
  |> filter(fn: (r) => r._field == "latency_ms" or r._field == "opcua_error")
  |> group(columns: ["_field"])
  |> mean()
'''
    try:
        with InfluxDBClient(url=url, token=token, org=org) as client:
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
