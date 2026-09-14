"""Capture-based recommendations for format / resolution / mono vs RGB."""

from __future__ import annotations

from collections import Counter


def build_recommendations(*, profile: dict, stats: dict) -> dict:
    cameras = profile.get("cameras") or []
    avg_size = float(stats.get("avg_bytes") or 0)
    count = int(stats.get("object_count") or 0)
    formats = Counter()
    colors = Counter()
    widths: list[int] = []
    for cam in cameras:
        capture = cam.get("capture") or {}
        formats[str(capture.get("image_format") or "png")] += 1
        colors[str(capture.get("color_mode") or "mono")] += 1
        if capture.get("width"):
            try:
                widths.append(int(capture["width"]))
            except (TypeError, ValueError):
                pass
    sample_formats = stats.get("formats") or {}
    sample_colors = stats.get("colorspaces") or {}
    for name, n in sample_formats.items():
        formats[str(name)] += int(n)
    for name, n in sample_colors.items():
        colors[str(name)] += int(n)

    recs: list[dict] = []
    if colors.get("mono", 0) >= colors.get("rgb", 0):
        recs.append(
            {
                "topic": "colorspace",
                "recommendation": "mono",
                "reason": "Mono reduces bandwidth and is sufficient for PatchCore surface/completeness when color is not a defect cue.",
            }
        )
    else:
        recs.append(
            {
                "topic": "colorspace",
                "recommendation": "rgb",
                "reason": "RGB/Bayer is configured on one or more views — keep RGB if color defects (wrong clip, label, coating) matter.",
            }
        )

    if avg_size > 2_500_000 and count:
        recs.append(
            {
                "topic": "format",
                "recommendation": "jpeg_archive_png_training",
                "reason": f"Average object size is {int(avg_size)} bytes. Use PNG for training/Gutteile, JPEG for 24h endurance archive.",
            }
        )
    else:
        recs.append(
            {
                "topic": "format",
                "recommendation": "png",
                "reason": "PNG is the default lossless format for Gutteil-Training and QA n.i.O. samples.",
            }
        )

    min_res = int((profile.get("acceptance") or {}).get("min_resolution_px") or 1280)
    if widths and min(widths) < min_res:
        recs.append(
            {
                "topic": "resolution",
                "recommendation": f">={min_res}px on the long edge",
                "reason": "A configured camera is below the station acceptance resolution.",
            }
        )
    else:
        recs.append(
            {
                "topic": "resolution",
                "recommendation": f">={min_res}px long edge (FOV must cover corners/edges/features)",
                "reason": "Acceptance criterion from the station profile. Confirm in the perspective checklist.",
            }
        )

    roles = {str(c.get("role")) for c in cameras if c.get("enabled", True)}
    if (profile.get("acceptance") or {}).get("require_bottom_view") and "bottom" not in roles:
        recs.append(
            {
                "topic": "perspective",
                "recommendation": "add_bottom_view",
                "reason": "Station acceptance requires a bottom camera slot (Unteransicht).",
            }
        )
    elif "bottom" not in roles:
        recs.append(
            {
                "topic": "perspective",
                "recommendation": "consider_bottom_view",
                "reason": "No bottom-view slot configured. Add a camera with role=bottom if the part underside is in scope.",
            }
        )

    recs.append(
        {
            "topic": "optics",
            "recommendation": "commission_on_station_profile",
            "reason": "Lens and lighting purchases follow the per-camera lens/FOV notes and lighting profile — not ad-hoc at the line.",
        }
    )

    return {
        "station_id": profile.get("station_id"),
        "sample_count": count,
        "avg_bytes": avg_size,
        "configured_cameras": len(cameras),
        "roles": sorted(roles),
        "formats": dict(formats),
        "colorspaces": dict(colors),
        "items": recs,
    }
