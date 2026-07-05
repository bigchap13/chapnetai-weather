from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

CUSTOM_CONCEPTS_FILE = Path("data/watchman_knowledge/custom_concepts.json")
APPROVED_CONCEPTS_LOG = Path("data/watchman_learning/approved_concepts.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return slug or "custom_concept"


def _load_file() -> Dict[str, Any]:
    CUSTOM_CONCEPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CUSTOM_CONCEPTS_FILE.exists():
        return {"concepts": {}}

    try:
        data = json.loads(CUSTOM_CONCEPTS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"concepts": {}}
        data.setdefault("concepts", {})
        return data
    except Exception:
        return {"concepts": {}}


def _save_file(data: Dict[str, Any]) -> None:
    CUSTOM_CONCEPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CUSTOM_CONCEPTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def list_custom_concepts() -> Dict[str, Any]:
    data = _load_file()
    return {
        "ok": True,
        "mode": "Watchman Custom Knowledge Concepts",
        "conceptCount": len(data.get("concepts", {})),
        "concepts": data.get("concepts", {}),
    }


def add_custom_concept(payload: Dict[str, Any]) -> Dict[str, Any]:
    label = str(payload.get("label") or payload.get("name") or "").strip()
    if not label:
        return {"ok": False, "error": "label_required"}

    concept_id = _slug(payload.get("conceptId") or label)

    terms = payload.get("terms") or []
    depends_on = payload.get("dependsOn") or []
    logic = str(payload.get("watchmanLogic") or payload.get("logic") or "").strip()

    if isinstance(terms, str):
        terms = [terms]
    if isinstance(depends_on, str):
        depends_on = [depends_on]

    concept = {
        "label": label,
        "terms": [str(x).strip() for x in terms if str(x).strip()],
        "dependsOn": [str(x).strip() for x in depends_on if str(x).strip()],
        "watchmanLogic": logic or f"{label} is a learned Watchman concept.",
        "source": "custom_learning",
        "createdAt": _now(),
    }

    data = _load_file()
    data.setdefault("concepts", {})[concept_id] = concept
    _save_file(data)

    APPROVED_CONCEPTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with APPROVED_CONCEPTS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now(), "conceptId": concept_id, "concept": concept}, ensure_ascii=False) + "\n")

    return {
        "ok": True,
        "mode": "Watchman Knowledge Growth",
        "conceptId": concept_id,
        "concept": concept,
        "message": "Custom concept saved. Watchman can use it without changing Python code.",
    }


def suggest_custom_concept_from_question(question: str) -> Dict[str, Any]:
    q = (question or "").strip()
    if not q:
        return {"ok": False, "error": "question_required"}

    words = re.findall(r"[a-z0-9']+", q.lower())
    useful = [w for w in words if len(w) >= 4 and w not in {"what", "when", "where", "should", "would", "could", "watchman", "today", "tonight", "tomorrow"}]

    label = " ".join(w.capitalize() for w in useful[:3]) or "Learned Question"

    return {
        "ok": True,
        "mode": "Watchman Concept Suggestion",
        "suggestedConcept": {
            "label": label,
            "terms": useful[:8],
            "dependsOn": ["weather_context", "user_goal", "timing"],
            "watchmanLogic": f"Learned from question: {q}",
        },
        "question": q,
    }
