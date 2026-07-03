from datetime import datetime, timezone

_MEMORY = []


def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def record_weather_memory(place, weather, mission=None, explanation=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []

    item = {
        "time": _now(),
        "place": place,
        "threatScore": _safe_int(watchman.get("threatScore"), 0),
        "threatLevel": watchman.get("threatLevel"),
        "precipChance": _safe_int(watchman.get("precipChance"), 0),
        "alertCount": len(alerts),
        "mission": mission,
        "explanation": explanation,
    }

    _MEMORY.append(item)
    _MEMORY[:] = _MEMORY[-100:]
    return item


def weather_memory_summary(place=None):
    rows = _MEMORY
    if place:
        key = str(place).lower()
        rows = [r for r in rows if str(r.get("place") or "").lower() == key]

    latest = rows[-1] if rows else None
    previous = rows[-2] if len(rows) >= 2 else None

    changes = []
    if latest and previous:
        ts = latest.get("threatScore", 0) - previous.get("threatScore", 0)
        pc = latest.get("precipChance", 0) - previous.get("precipChance", 0)
        ac = latest.get("alertCount", 0) - previous.get("alertCount", 0)

        if ts:
            changes.append(f"Threat score changed by {ts:+d}.")
        if pc:
            changes.append(f"Rain chance changed by {pc:+d}%.")
        if ac:
            changes.append(f"Alert count changed by {ac:+d}.")

    return {
        "mode": "Watchman Weather Memory Timeline V1",
        "count": len(rows),
        "latest": latest,
        "previous": previous,
        "changes": changes or ["No meaningful timeline change detected yet."],
        "timeline": rows[-12:],
    }
