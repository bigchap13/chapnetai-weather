from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

FEEDBACK_DIR = Path("data/watchman_learning")
FEEDBACK_LOG = FEEDBACK_DIR / "feedback_log.jsonl"

FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_feedback(row: Dict[str, Any]) -> Dict[str, Any]:
    row = {
        "ts": _now(),
        "question": row.get("question") or "",
        "answer": row.get("answer") or "",
        "rating": row.get("rating") or "",
        "feedback": row.get("feedback") or "",
        "leadSkill": row.get("leadSkill") or "",
        "overallDecision": row.get("overallDecision") or "",
        "confidence": row.get("confidence"),
    }

    with FEEDBACK_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {
        "ok": True,
        "mode": "Watchman Feedback Engine",
        "saved": row,
    }


def read_feedback(limit: int = 100) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []

    if FEEDBACK_LOG.exists():
        for line in FEEDBACK_LOG.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    return {
        "ok": True,
        "mode": "Watchman Feedback Review",
        "count": len(rows),
        "feedback": rows,
    }


def feedback_summary() -> Dict[str, Any]:
    rows = read_feedback(10000)["feedback"]

    total = len(rows)
    good = sum(1 for r in rows if str(r.get("rating")).lower() in {"good", "helpful", "yes", "right"})
    bad = sum(1 for r in rows if str(r.get("rating")).lower() in {"bad", "wrong", "no", "not_helpful"})
    unclear = total - good - bad

    success_rate = round((good / total) * 100, 1) if total else 0

    weak_examples = [
        {
            "question": r.get("question"),
            "rating": r.get("rating"),
            "feedback": r.get("feedback"),
            "leadSkill": r.get("leadSkill"),
        }
        for r in rows
        if str(r.get("rating")).lower() in {"bad", "wrong", "no", "not_helpful"}
    ][-20:]

    return {
        "ok": True,
        "mode": "Watchman Feedback Summary V1",
        "totalFeedback": total,
        "goodFeedback": good,
        "badFeedback": bad,
        "unclearFeedback": unclear,
        "successRate": success_rate,
        "weakExamples": weak_examples,
    }
