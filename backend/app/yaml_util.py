"""Minimal YAML dump/load for station templates (no PyYAML dependency)."""

from __future__ import annotations

from typing import Any


def dumps(value: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(value, dict):
        if not value:
            return "{}\n" if indent == 0 else "{}"
        lines: list[str] = []
        for key, item in value.items():
            rendered = dumps(item, indent + 1)
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                if rendered.strip():
                    lines.append(rendered.rstrip("\n") if rendered.endswith("\n") else rendered)
            else:
                lines.append(f"{pad}{key}: {rendered.strip()}")
        text = "\n".join(lines)
        return text + ("\n" if indent == 0 else "")
    if isinstance(value, list):
        if not value:
            return "[]"
        lines = []
        for item in value:
            rendered = dumps(item, indent + 1)
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(rendered.rstrip("\n"))
            else:
                lines.append(f"{pad}- {rendered.strip()}")
        return "\n".join(lines)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if any(ch in text for ch in ":#{}[]&*!|>'\"%@`") or text.strip() != text or "\n" in text:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def loads(text: str) -> Any:
    """Parse a restricted YAML subset (mappings, lists, scalars)."""
    lines = text.replace("\t", "  ").splitlines()
    cleaned = [ln.rstrip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    if not cleaned:
        return {}
    value, _ = _parse_block(cleaned, 0, 0)
    return value


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if text in {"null", "~", ""}:
        return None
    if text in {"true", "True", "yes"}:
        return True
    if text in {"false", "False", "no"}:
        return False
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _parse_block(lines: list[str], index: int, min_indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    indent = _indent(lines[index])
    if indent < min_indent:
        return {}, index
    if lines[index].lstrip().startswith("-"):
        return _parse_list(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_map(lines: list[str], index: int, indent: int) -> tuple[dict, int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line = lines[index]
        cur = _indent(line)
        if cur < indent:
            break
        if cur > indent:
            raise ValueError(f"Unexpected indent at line: {line}")
        if line.lstrip().startswith("-"):
            break
        if ":" not in line:
            raise ValueError(f"Expected mapping line: {line}")
        key, rest = line.strip().split(":", 1)
        rest = rest.strip()
        index += 1
        if rest:
            result[key] = _parse_scalar(rest)
            continue
        if index < len(lines) and _indent(lines[index]) > indent:
            child, index = _parse_block(lines, index, indent + 1)
            result[key] = child
        else:
            result[key] = None
    return result, index


def _parse_list(lines: list[str], index: int, indent: int) -> tuple[list, int]:
    items: list[Any] = []
    while index < len(lines):
        line = lines[index]
        cur = _indent(line)
        if cur < indent:
            break
        stripped = line.lstrip()
        if not stripped.startswith("-"):
            break
        rest = stripped[1:].strip()
        index += 1
        if rest:
            if ":" in rest and not (rest.startswith('"') or rest.startswith("'")):
                key, value = rest.split(":", 1)
                nested = {key: _parse_scalar(value)}
                if index < len(lines) and _indent(lines[index]) > indent:
                    extra, index = _parse_map(lines, index, _indent(lines[index]))
                    nested.update(extra)
                items.append(nested)
            else:
                items.append(_parse_scalar(rest))
        else:
            child, index = _parse_block(lines, index, indent + 1)
            items.append(child)
    return items, index
