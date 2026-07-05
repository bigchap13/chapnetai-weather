from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

LEARNING_DIR = Path("data/watchman_learning")
QUESTION_LOG = LEARNING_DIR / "question_log.jsonl"
WEAK_QUESTIONS = LEARNING_DIR / "weak_questions.jsonl"

LEARNING_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def record_question(question: str, brain_result: Dict[str, Any]) -> Dict[str, Any]:
    routing = brain_result.get("routing") or {}
    synthesis = brain_result.get("synthesis") or {}

    row = {
        "ts": _now(),
        "question": question,
        "cleanedQuestion": routing.get("cleanedQuestion"),
        "leadSkill": (routing.get("leadSkill") or {}).get("domain"),
        "supportingSkills": [x.get("domain") for x in routing.get("supportingSkills") or []],
        "multiSkill": routing.get("multiSkill"),
        "overallDecision": synthesis.get("overallDecision"),
        "confidence": synthesis.get("confidence"),
        "answer": brain_result.get("answer"),
    }

    append_jsonl(QUESTION_LOG, row)

    confidence = synthesis.get("confidence") or 0
    decision = synthesis.get("overallDecision") or ""

    if confidence < 60 or decision == "needs_more_context":
        append_jsonl(WEAK_QUESTIONS, row)

    return row


def read_recent_questions(limit: int = 50) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []

    if QUESTION_LOG.exists():
        lines = QUESTION_LOG.read_text(encoding="utf-8").splitlines()[-limit:]
        for line in lines:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    return {
        "ok": True,
        "mode": "Watchman Learning Memory",
        "count": len(rows),
        "questions": rows,
    }


def read_weak_questions(limit: int = 50) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []

    if WEAK_QUESTIONS.exists():
        lines = WEAK_QUESTIONS.read_text(encoding="utf-8").splitlines()[-limit:]
        for line in lines:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    return {
        "ok": True,
        "mode": "Watchman Weak Question Review",
        "count": len(rows),
        "questions": rows,
    }


def learning_summary() -> Dict[str, Any]:
    total = 0
    weak = 0

    if QUESTION_LOG.exists():
        total = len(QUESTION_LOG.read_text(encoding="utf-8").splitlines())

    if WEAK_QUESTIONS.exists():
        weak = len(WEAK_QUESTIONS.read_text(encoding="utf-8").splitlines())

    return {
        "ok": True,
        "mode": "Watchman Learning Memory V1",
        "totalQuestionsLogged": total,
        "weakQuestionsLogged": weak,
        "purpose": "Logs real user questions, routing decisions, confidence, and weak spots so Watchman can keep improving.",
    }
