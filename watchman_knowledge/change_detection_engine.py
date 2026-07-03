from datetime import datetime, timezone

_LAST_BY_PLACE = {}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _key(place):
    return str(place or "default").strip().lower()


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def _snapshot(place, weather, storm_arrival=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    forecast = weather.get("forecast") or []
    first = forecast[0] if forecast and isinstance(forecast[0], dict) else {}

    return {
        "time": _now(),
        "place": place,
        "alerts": len(weather.get("alerts") or []),
        "threatScore": _safe_int(watchman.get("threatScore"), 0),
        "threatLevel": watchman.get("threatLevel"),
        "precipChance": _safe_int(watchman.get("precipChance"), 0),
        "travelIndex": _safe_int(watchman.get("travelIndex"), 0),
        "outdoorIndex": _safe_int(watchman.get("outdoorIndex"), 0),
        "condition": first.get("shortForecast"),
        "stormArrival": (storm_arrival or {}).get("arrivalEstimate") if isinstance(storm_arrival, dict) else None,
        "stormStatus": (storm_arrival or {}).get("status") if isinstance(storm_arrival, dict) else None,
    }


def detect_weather_changes(place, weather, storm_arrival=None):
    snap = _snapshot(place, weather, storm_arrival)
    old = _LAST_BY_PLACE.get(_key(place))
    _LAST_BY_PLACE[_key(place)] = snap

    if not old:
        return {
            "mode": "Watchman Change Detection Engine V1",
            "status": "first_scan",
            "changes": ["First scan for this location. Future scans will show what changed."],
            "previous": None,
            "current": snap,
            "answer": "Change Detection V1: First scan for this location. Future scans will show what changed.",
        }

    changes = []

    if snap["alerts"] > old["alerts"]:
        changes.append(f"alert count increased from {old['alerts']} to {snap['alerts']}")
    elif snap["alerts"] < old["alerts"]:
        changes.append(f"alert count decreased from {old['alerts']} to {snap['alerts']}")

    diff = snap["threatScore"] - old["threatScore"]
    if diff >= 10:
        changes.append(f"threat score rose from {old['threatScore']} to {snap['threatScore']}")
    elif diff <= -10:
        changes.append(f"threat score dropped from {old['threatScore']} to {snap['threatScore']}")

    pdiff = snap["precipChance"] - old["precipChance"]
    if pdiff >= 15:
        changes.append(f"precipitation chance increased from {old['precipChance']}% to {snap['precipChance']}%")
    elif pdiff <= -15:
        changes.append(f"precipitation chance decreased from {old['precipChance']}% to {snap['precipChance']}%")

    if snap["condition"] != old["condition"]:
        changes.append(f"forecast changed from {old['condition']} to {snap['condition']}")

    if snap["stormArrival"] != old["stormArrival"]:
        changes.append(f"storm arrival estimate changed from {old['stormArrival']} to {snap['stormArrival']}")

    status = "changed" if changes else "steady"

    return {
        "mode": "Watchman Change Detection Engine V1",
        "status": status,
        "changes": changes or ["No meaningful change detected."],
        "previous": old,
        "current": snap,
        "answer": f"Change Detection V1: {'; '.join(changes or ['No meaningful change detected.'])}",
    }


def change_detection_summary():
    return {
        "mode": "Watchman Change Detection Engine V1",
        "trackedPlaces": list(_LAST_BY_PLACE.keys()),
        "latest": list(_LAST_BY_PLACE.values())[-10:],
    }
