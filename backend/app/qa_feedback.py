from __future__ import annotations

from pathlib import Path

from .nio_store import persist_nio_sample, retract_nio_sample


def apply_qa_verdict(
    *,
    repo,
    data_root: Path,
    inspection_id: str,
    verdict: str,
    actor: str,
    feedback_id: str,
    comment: str = "",
) -> dict:
    """Rewrite inspection display/processing when QA confirms a defect as NIO."""
    item = repo.get(inspection_id) if repo is not None and hasattr(repo, "get") else None
    result: dict = {
        "inspection": item,
        "nio_sample": None,
        "decision_override": None,
    }
    if not item:
        return result

    qa_prev = item.get("qa") if isinstance(item.get("qa"), dict) else {}
    auto_decision = qa_prev.get("auto_decision") or item.get("decision") or "green"
    qa = {
        "auto_decision": auto_decision,
        "verdict": verdict,
        "actor": actor,
        "feedback_id": feedback_id,
        "comment": comment,
        "pending": verdict == "needs_review",
        "override": None,
    }

    if verdict == "confirm_anomaly":
        item["decision"] = "red"
        inference = dict(item.get("inference") or {})
        inference["status"] = "anomaly"
        if str(inference.get("defect_class") or "none") in {"", "none"}:
            inference["defect_class"] = "qa_confirmed_anomaly"
        item["inference"] = inference
        qa["override"] = "nio"
        qa["pending"] = False
        nio = persist_nio_sample(
            data_root=data_root,
            inspection=item,
            feedback_id=feedback_id,
            actor=actor,
        )
        result["nio_sample"] = nio
        result["decision_override"] = "red"
    elif verdict == "false_positive":
        item["decision"] = auto_decision
        qa["override"] = None
        qa["pending"] = False
        retract_nio_sample(data_root, inspection_id)
    else:
        item["decision"] = auto_decision
        qa["pending"] = True

    item["qa"] = qa
    if hasattr(repo, "update"):
        repo.update(item)
    result["inspection"] = item
    return result
