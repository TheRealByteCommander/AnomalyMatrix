"""MQTT trigger subscriber for SPS / MES start-inspection messages.

Works alongside OPC-UA. Disabled unless MQTT_ENABLED is truthy.
Payload parsing is independent of a live broker so tests and commissioning
can inject messages via POST /api/v1/triggers/mqtt.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from .epc import extract_from_mapping

logger = logging.getLogger(__name__)

TriggerHandler = Callable[[dict], dict]


@dataclass
class MqttStatus:
    enabled: bool = False
    connected: bool = False
    broker: str = ""
    port: int = 1883
    topic: str = ""
    last_message_at: str | None = None
    last_error: str | None = None
    last_epc: str | None = None
    last_action: str | None = None
    received: int = 0
    triggered: int = 0
    reconnects: int = 0


_status = MqttStatus()
_handler: TriggerHandler | None = None
_thread: threading.Thread | None = None
_stop = threading.Event()
_lock = threading.Lock()


def mqtt_enabled() -> bool:
    return os.getenv("MQTT_ENABLED", "").strip().lower() in {"1", "true", "yes"}


def mqtt_config() -> dict:
    return {
        "enabled": mqtt_enabled(),
        "broker": os.getenv("MQTT_BROKER", "127.0.0.1").strip() or "127.0.0.1",
        "port": int(os.getenv("MQTT_PORT", "1883") or 1883),
        "topic": os.getenv("MQTT_TOPIC", "anomalymatrix/eol/trigger").strip()
        or "anomalymatrix/eol/trigger",
        "username": os.getenv("MQTT_USERNAME", "").strip() or None,
        "qos": int(os.getenv("MQTT_QOS", "1") or 1),
        "client_id": os.getenv("MQTT_CLIENT_ID", "anomalymatrix-eol").strip()
        or "anomalymatrix-eol",
        "tls": os.getenv("MQTT_TLS", "").strip().lower() in {"1", "true", "yes"},
    }


def status_snapshot() -> dict:
    with _lock:
        cfg = mqtt_config()
        return {
            "enabled": _status.enabled,
            "connected": _status.connected,
            "broker": _status.broker or cfg["broker"],
            "port": _status.port or cfg["port"],
            "topic": _status.topic or cfg["topic"],
            "last_message_at": _status.last_message_at,
            "last_error": _status.last_error,
            "last_epc": _status.last_epc,
            "last_action": _status.last_action,
            "received": _status.received,
            "triggered": _status.triggered,
            "reconnects": _status.reconnects,
            "opcua_also_enabled": True,
        }


def set_trigger_handler(handler: TriggerHandler | None) -> None:
    global _handler
    _handler = handler


def parse_mqtt_payload(raw: Any) -> dict:
    """Map topic payload → inspection trigger.

    Accepts JSON objects, JSON strings, or UTF-8 text. Configurable field
    names via MQTT_ACTION_FIELD / MQTT_EPC_FIELD.
    """
    data: Any = raw
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            data = {}
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {"action": "inspect", "epc": text}

    if not isinstance(data, dict):
        data = {"value": data}

    ids = extract_from_mapping(data)
    action_field = os.getenv("MQTT_ACTION_FIELD", "action").strip() or "action"
    epc_field = os.getenv("MQTT_EPC_FIELD", "epc").strip() or "epc"
    action_raw = data.get(action_field) or data.get("command") or data.get("trigger") or data.get("event")
    action = str(action_raw or "inspect").strip().lower()
    if action in {"start", "start_inspection", "run", "inspect", "true", "1"}:
        action = "inspect"
    elif action in {"capture", "grab", "image"}:
        action = "capture"
    else:
        action = "inspect"

    epc = ids.get("epc") or data.get(epc_field)
    camera_ids = ids.get("camera_ids")
    if isinstance(camera_ids, str):
        camera_ids = [c.strip() for c in camera_ids.split(",") if c.strip()]
    camera_id = ids.get("camera_id") or data.get("camera")

    return {
        "action": action,
        "epc": epc,
        "process_id": ids.get("process_id"),
        "serial": ids.get("serial"),
        "lot_id": ids.get("lot_id"),
        "work_order": ids.get("work_order"),
        "recipe_id": ids.get("recipe_id") or data.get("recipe") or "recipe-default",
        "station_id": ids.get("station_id"),
        "camera_id": camera_id,
        "camera_ids": camera_ids if isinstance(camera_ids, list) else None,
        "source": "mqtt",
        "raw": data,
    }


def handle_parsed_trigger(parsed: dict) -> dict:
    if _handler is None:
        raise RuntimeError("MQTT trigger handler is not registered")
    result = _handler(parsed)
    with _lock:
        _status.triggered += 1
        _status.last_epc = parsed.get("epc")
        _status.last_action = parsed.get("action")
        _status.last_message_at = datetime.now(timezone.utc).isoformat()
    return result


def ingest_message(raw: Any) -> dict:
    with _lock:
        _status.received += 1
    parsed = parse_mqtt_payload(raw)
    return handle_parsed_trigger(parsed)


def _client_loop() -> None:
    cfg = mqtt_config()
    with _lock:
        _status.enabled = True
        _status.broker = str(cfg["broker"])
        _status.port = int(cfg["port"])
        _status.topic = str(cfg["topic"])
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning("paho-mqtt not installed — MQTT subscriber disabled")
        with _lock:
            _status.last_error = "paho-mqtt missing"
        return

    def on_connect(client, _userdata, _flags, reason_code, _properties=None):
        ok = reason_code == 0 or str(reason_code) in {"Success", "0"}
        with _lock:
            _status.connected = bool(ok)
            if not ok:
                _status.last_error = f"connect rc={reason_code}"
            else:
                _status.last_error = None
        if ok:
            client.subscribe(cfg["topic"], qos=int(cfg["qos"]))
            logger.info("MQTT subscribed topic=%s broker=%s", cfg["topic"], cfg["broker"])

    def on_disconnect(client, _userdata, _flags, reason_code, _properties=None):
        with _lock:
            _status.connected = False
            _status.reconnects += 1
            _status.last_error = f"disconnect rc={reason_code}"
        logger.warning("MQTT disconnected rc=%s — auto-reconnect", reason_code)

    def on_message(_client, _userdata, message):
        try:
            ingest_message(message.payload)
        except Exception as exc:
            logger.exception("MQTT trigger failed: %s", exc)
            with _lock:
                _status.last_error = str(exc.__class__.__name__)

    client_kwargs = {"client_id": str(cfg["client_id"])}
    try:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            **client_kwargs,
        )
    except (TypeError, AttributeError):
        client = mqtt.Client(**client_kwargs)
    user = cfg.get("username")
    password = os.getenv("MQTT_PASSWORD", "")
    if user:
        client.username_pw_set(user, password or None)
    if cfg.get("tls"):
        client.tls_set()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    while not _stop.is_set():
        try:
            client.connect(str(cfg["broker"]), int(cfg["port"]), keepalive=30)
            client.loop_start()
            while not _stop.wait(2.0):
                if not _status.connected:
                    break
            client.loop_stop()
            try:
                client.disconnect()
            except Exception:
                pass
        except Exception as exc:
            logger.warning("MQTT connect failed: %s", exc)
            with _lock:
                _status.connected = False
                _status.last_error = str(exc.__class__.__name__)
                _status.reconnects += 1
            _stop.wait(5.0)


def start_subscriber() -> None:
    global _thread
    if not mqtt_enabled():
        with _lock:
            _status.enabled = False
            _status.connected = False
        return
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_client_loop, name="amx-mqtt", daemon=True)
    _thread.start()


def stop_subscriber() -> None:
    _stop.set()
