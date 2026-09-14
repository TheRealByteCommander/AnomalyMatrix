"""Configurable PNG/JPEG encoding with RAW passthrough hook."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_FORMATS = ("png", "jpeg", "jpg", "raw")
RAW_LIMITATION = (
    "RAW passthrough stores camera/driver bytes only when the capture payload "
    "includes raw_bytes / image_raw. Synthetic and OpenCV paths emit PNG/JPEG; "
    "GigE/GenICam RAW is a driver hook (CAMERA_PIXEL_FORMAT=BayerRG8/Mono12) "
    "and is not decoded by PatchCore."
)


@dataclass
class EncodedImage:
    data: bytes
    format: str
    content_type: str
    colorspace: str
    width: int | None
    height: int | None
    raw_passthrough: bool
    limitation: str | None = None


def normalize_format(value: str | None, default: str = "png") -> str:
    fmt = (value or default).strip().lower()
    if fmt == "jpg":
        fmt = "jpeg"
    if fmt not in {"png", "jpeg", "raw"}:
        return default
    return fmt


def encode_frame(frame: dict, *, image_format: str = "png", jpeg_quality: int = 92) -> EncodedImage:
    fmt = normalize_format(image_format)
    width = frame.get("image_width")
    height = frame.get("image_height")
    colorspace = str(frame.get("colorspace") or frame.get("pixel_format") or "unknown")

    if fmt == "raw":
        raw = frame.get("raw_bytes") or frame.get("image_raw")
        if isinstance(raw, (bytes, bytearray)) and raw:
            return EncodedImage(
                data=bytes(raw),
                format="raw",
                content_type="application/octet-stream",
                colorspace=colorspace,
                width=width,
                height=height,
                raw_passthrough=True,
            )
        # Fallback: encode PNG and document the limitation.
        png = _encode_numpy_or_b64(frame, "png", jpeg_quality)
        return EncodedImage(
            data=png or b"",
            format="png",
            content_type="image/png",
            colorspace=colorspace,
            width=width,
            height=height,
            raw_passthrough=False,
            limitation=RAW_LIMITATION,
        )

    data = _encode_numpy_or_b64(frame, fmt, jpeg_quality) or b""
    return EncodedImage(
        data=data,
        format=fmt,
        content_type="image/jpeg" if fmt == "jpeg" else "image/png",
        colorspace=colorspace,
        width=width,
        height=height,
        raw_passthrough=False,
    )


def _encode_numpy_or_b64(frame: dict, fmt: str, jpeg_quality: int) -> bytes | None:
    try:
        import cv2
        import numpy as np
    except Exception:
        return _from_b64(frame)

    gray = None
    array = frame.get("image_array")
    if array is not None:
        try:
            gray = np.asarray(array)
        except Exception:
            gray = None
    if gray is None:
        b64 = frame.get("image_b64")
        if b64:
            import base64

            arr = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
            gray = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if gray is None:
        return _from_b64(frame)
    if gray.ndim == 2:
        colorspace = "mono"
    else:
        colorspace = "rgb"
        frame.setdefault("colorspace", colorspace)
    ext = ".jpg" if fmt == "jpeg" else ".png"
    params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)] if fmt == "jpeg" else []
    ok, buf = cv2.imencode(ext, gray, params)
    if not ok:
        return None
    frame.setdefault("image_width", int(gray.shape[1]))
    frame.setdefault("image_height", int(gray.shape[0]))
    if "colorspace" not in frame:
        frame["colorspace"] = "mono" if gray.ndim == 2 else "rgb"
    return buf.tobytes()


def _from_b64(frame: dict) -> bytes | None:
    b64 = frame.get("image_b64")
    if not b64:
        return None
    import base64

    return base64.b64decode(b64)
