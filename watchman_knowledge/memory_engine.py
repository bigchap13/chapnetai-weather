from datetime import datetime, timezone

_SESSION_MEMORY = {}


def _key(place):
    return str(place or "default").strip().lower()


def remember_scan(place, question, answer, weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    forecast = weather.get("forecast") or []
    first = forecast[0] if forecast and isinstance(forecast[0], dict) else {}

    item = {
        "time": datetime.now(timezone.utc).isoformat(),
        "question": question or "",
        "answer": answer or "",
        "threatLevel": watchman.get("threatLevel"),
        "threatScore": watchman.get("threatScore"),
        "outdoorIndex": watchman.get("outdoorIndex"),
        "travelIndex": watchman.get("travelIndex"),
        "precipChance": ((first.get("probabilityOfPrecipitation") or {}).get("value")),
        "condition": first.get("shortForecast"),
        "alerts": len(weather.get("alerts") or []),
    }

    k = _key(place)
    _SESSION_MEMORY.setdefault(k, []).append(item)
    _SESSION_MEMORY[k] = _SESSION_MEMORY[k][-20:]
    return item


def memory_summary(place):
    rows = _SESSION_MEMORY.get(_key(place), [])
    if not rows:
        return {
            "status": "empty",
            "summary": "No previous Watchman memory for this location in this session.",
            "recentQuestions": [],
            "trend": "unknown",
        }

    first = rows[0]
    last = rows[-1]

    trend = "steady"
    try:
        diff = int(last.get("threatScore") or 0) - int(first.get("threatScore") or 0)
        if diff >= 10:
            trend = "worsening"
        elif diff <= -10:
            trend = "improving"
    except Exception:
        diff = 0

    return {
        "status": "active",
        "summary": f"Watchman remembers {len(rows)} scan(s) for this location this session. Threat trend is {trend}.",
        "recentQuestions": [r["question"] for r in rows[-5:] if r.get("question")],
        "trend": trend,
        "threatScoreChange": diff,
        "lastScan": last,
    }
