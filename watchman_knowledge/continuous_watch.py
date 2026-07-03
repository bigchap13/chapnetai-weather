from datetime import datetime, timezone

_WATCHES = {}


def _key(place):
    return str(place or "default").strip().lower()


def continuous_watch_answer(question, place, weather):
    q = str(question or "").lower()
    place = place or "selected location"
    weather = weather or {}
    watchman = weather.get("watchman") or {}

    start_triggers = [
        "watch my house",
        "watch this location",
        "watch my route",
        "watch my campsite",
        "watch this place",
        "monitor my house",
        "monitor this location",
        "continuous watch",
        "start watch",
    ]

    status_triggers = [
        "watch status",
        "what are you watching",
        "are you watching",
        "anything changed",
        "has anything changed",
    ]

    if any(t in q for t in start_triggers):
        item = {
            "place": place,
            "started": datetime.now(timezone.utc).isoformat(),
            "threatLevel": watchman.get("threatLevel"),
            "threatScore": watchman.get("threatScore"),
            "alerts": len(weather.get("alerts") or []),
            "condition": ((weather.get("forecast") or [{}])[0] or {}).get("shortForecast"),
        }
        _WATCHES[_key(place)] = item

        return {
            "mode": "Watchman Continuous Watch Mode",
            "status": "started",
            "watch": item,
            "answer": (
                f"Continuous Watch Mode started for {place}. "
                f"Current threat level is {item.get('threatLevel')} with score {item.get('threatScore')}. "
                f"Watchman will compare future checks against this baseline during this server session."
            ),
        }

    if any(t in q for t in status_triggers):
        old = _WATCHES.get(_key(place))
        if not old:
            return {
                "mode": "Watchman Continuous Watch Mode",
                "status": "not_started",
                "answer": f"No Continuous Watch is active for {place} in this server session.",
            }

        current_score = watchman.get("threatScore")
        current_alerts = len(weather.get("alerts") or [])

        changes = []
        if str(current_score) != str(old.get("threatScore")):
            changes.append(f"threat score changed from {old.get('threatScore')} to {current_score}")
        if current_alerts != old.get("alerts"):
            changes.append(f"alert count changed from {old.get('alerts')} to {current_alerts}")

        return {
            "mode": "Watchman Continuous Watch Mode",
            "status": "active",
            "changes": changes or ["no major change detected"],
            "baseline": old,
            "answer": (
                f"Continuous Watch status for {place}: "
                f"{'; '.join(changes or ['no major change detected'])}."
            ),
        }

    return None
