"""Station camera count limits.

Certified sequential path remains 1–4. Operators may raise AMX_MAX_CAMERAS
(up to HARD_CAP) for additional views (e.g. bottom / STF) without a code fork.
"""

from __future__ import annotations

import os

MIN_CAMERAS = 1
CERTIFIED_MAX_CAMERAS = 4
HARD_CAP = 16
DEFAULT_MAX_CAMERAS = 4


def max_cameras() -> int:
    raw = os.getenv("AMX_MAX_CAMERAS", str(DEFAULT_MAX_CAMERAS)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = DEFAULT_MAX_CAMERAS
    return max(MIN_CAMERAS, min(HARD_CAP, value))
