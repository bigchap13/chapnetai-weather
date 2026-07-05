from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

MEMORY_FILE = Path("data/watchman_learning/conversation_memory.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict[str, Any]:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        return {"turns": [], "facts": {}}
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        data.setdefault("turns", [])
        data.setdefault("facts", {})
        return data
    except Exception:
        return {"turns": [], "facts": {}}


def _save(data: Dict[str, Any]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _extract_facts(question: str, result: Dict[str, Any]) -> Dict[str, Any]:
    q = question or ""
    facts: Dict[str, Any] = {}

    m = re.search(r"\bto\s+([A-Z][A-Za-z .'-]+?)(?:\s+tonight|\s+today|\s+tomorrow|\?|$)", q)
    if m:
        facts["lastDestination"] = m.group(1).strip()

    highways = re.findall(r"\b(?:I|US)[-\s]?\d{1,3}\b", q, flags=re.I)
    if highways:
        facts["lastHighways"] = [h.upper().replace(" ", "-") for h in highways]

    routing = result.get("routing") or {}
    lead = (routing.get("leadSkill") or {}).get("domain")
    if lead:
        facts["lastLeadSkill"] = lead

    synthesis = result.get("synthesis") or {}
    if synthesis:
        facts["lastDecision"] = synthesis.get("overallDecision")
        facts["lastConfidence"] = synthesis.get("confidence")

    return {k: v for k, v in facts.items() if v}


def remember_turn(question: str, result: Dict[str, Any]) -> Dict[str, Any]:
    data = _load()
    turn = {
        "ts": _now(),
        "question": question,
        "answer": result.get("answer"),
        "leadSkill": ((result.get("routing") or {}).get("leadSkill") or {}).get("domain"),
        "decision": (result.get("synthesis") or {}).get("overallDecision"),
        "confidence": (result.get("synthesis") or {}).get("confidence"),
    }

    data["turns"].append(turn)
    data["turns"] = data["turns"][-20:]

    data["facts"].update(_extract_facts(question, result))
    data["facts"]["lastQuestion"] = question
    data["facts"]["lastAnswer"] = result.get("answer")
    data["facts"]["updatedAt"] = _now()

    _save(data)

    return {
        "ok": True,
        "mode": "Watchman Conversation Memory",
        "remembered": turn,
        "facts": data["facts"],
    }


def conversation_context() -> Dict[str, Any]:
    data = _load()
    return {
        "ok": True,
        "mode": "Watchman Conversation Context V1",
        "turnCount": len(data.get("turns", [])),
        "facts": data.get("facts", {}),
        "recentTurns": data.get("turns", [])[-10:],
    }


def clear_conversation_memory() -> Dict[str, Any]:
    data = {"turns": [], "facts": {}}
    _save(data)
    return {"ok": True, "mode": "Watchman Conversation Memory Cleared"}
