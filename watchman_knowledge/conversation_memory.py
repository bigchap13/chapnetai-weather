from datetime import datetime, timezone

_MEMORY = {}


def _key(place):
    return str(place or "default").strip().lower()


def remember_conversation(place, question, answer, weather, reasoning=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}

    item = {
        "time": datetime.now(timezone.utc).isoformat(),
        "question": question or "",
        "answer": answer or "",
        "threatLevel": watchman.get("threatLevel"),
        "threatScore": watchman.get("threatScore"),
        "reasoningConclusion": (reasoning or {}).get("conclusion") if isinstance(reasoning, dict) else None,
    }

    k = _key(place)
    _MEMORY.setdefault(k, []).append(item)
    _MEMORY[k] = _MEMORY[k][-30:]
    return item


def conversation_memory_summary(place):
    rows = _MEMORY.get(_key(place), [])

    if not rows:
        return {
            "mode": "Watchman Conversation Memory",
            "status": "empty",
            "summary": "No conversation memory is available for this location yet.",
            "recentQuestions": [],
        }

    first = rows[0]
    last = rows[-1]

    try:
        diff = int(last.get("threatScore") or 0) - int(first.get("threatScore") or 0)
    except Exception:
        diff = 0

    if diff >= 10:
        trend = "worsening"
    elif diff <= -10:
        trend = "improving"
    else:
        trend = "steady"

    return {
        "mode": "Watchman Conversation Memory",
        "status": "active",
        "summary": f"Watchman remembers {len(rows)} recent exchange(s) for this location. Threat trend is {trend}.",
        "trend": trend,
        "threatScoreChange": diff,
        "recentQuestions": [r["question"] for r in rows[-6:] if r.get("question")],
        "lastExchange": last,
    }


def memory_answer(question, place):
    q = str(question or "").lower()

    if not any(x in q for x in ["earlier", "last time", "previous", "remember", "what did you say", "has anything changed"]):
        return None

    summary = conversation_memory_summary(place)

    if summary["status"] == "empty":
        answer = "I do not have prior Watchman conversation memory for this location in this session yet."
    else:
        answer = (
            f"{summary['summary']} Recent questions: "
            f"{'; '.join(summary['recentQuestions'][-4:])}. "
            f"Threat score change: {summary['threatScoreChange']}."
        )

    return {
        "mode": "Watchman Conversation Memory",
        "answer": answer,
        "summary": summary,
    }
