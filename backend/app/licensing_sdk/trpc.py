"""Helpers for tRPC + superjson wire format used by the license server."""

from typing import Any, Dict, Optional, Tuple


def wrap_input(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"json": payload}


def unwrap_result(response_json: Dict[str, Any]) -> Dict[str, Any]:
    data = response_json.get("result", {}).get("data", {})
    if isinstance(data, dict) and "json" in data:
        return data["json"] or {}
    return data if isinstance(data, dict) else {}


def unwrap_error(response_json: Dict[str, Any]) -> Tuple[str, str]:
    error = response_json.get("error", {})
    if isinstance(error, dict) and "json" in error:
        error = error["json"] or {}

    message = error.get("message", "Licensing API error")
    data = error.get("data") if isinstance(error.get("data"), dict) else {}
    code = data.get("code") or error.get("code") or "UNKNOWN"
    return str(code), str(message)


def raise_for_trpc_error(response_json: Dict[str, Any], http_ok: bool = True) -> None:
    if http_ok and "error" not in response_json:
        return

    code, message = unwrap_error(response_json)
    raise Exception(f"[{code}] {message}")
