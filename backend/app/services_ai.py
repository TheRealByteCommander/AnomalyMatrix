from __future__ import annotations

import hashlib


def infer_stub(frame: dict) -> dict:
    fingerprint = f"{frame.get('frame_id','')}-{frame.get('camera_id','')}-{frame.get('recipe_id','')}"
    digest = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
    score_raw = int(digest[:8], 16) / 0xFFFFFFFF
    anomaly_score = round(score_raw, 4)

    status = "anomaly" if anomaly_score >= 0.7 else "normal"
    heatmap_uri = f"synthetic://heatmap/{frame.get('frame_id','unknown')}.png"

    return {
        "anomaly_score": anomaly_score,
        "status": status,
        "heatmap_uri": heatmap_uri,
        "model_version": "patchcore-mvp-v0",
    }
