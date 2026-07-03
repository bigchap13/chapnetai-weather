_LAST_ALERT_STATE = {}


def _key(place):
    return str(place or "default").strip().lower()


def _alert_signature(alert):
    if not isinstance(alert, dict):
        return ""

    return "|".join([
        str(alert.get("id") or alert.get("@id") or alert.get("identifier") or ""),
        str(alert.get("event") or ""),
        str(alert.get("headline") or ""),
        str(alert.get("areaDesc") or ""),
        str(alert.get("effective") or ""),
        str(alert.get("expires") or ""),
    ])


def alert_change_notifier(place, weather, storm_arrival=None):
    weather = weather or {}
    alerts = weather.get("alerts") or []
    watchman = weather.get("watchman") or {}

    signatures = sorted([_alert_signature(a) for a in alerts if isinstance(a, dict)])
    state = {
        "alertCount": len(alerts),
        "alertSignatures": signatures,
        "threatScore": watchman.get("threatScore"),
        "threatLevel": watchman.get("threatLevel"),
        "stormStatus": (storm_arrival or {}).get("status") if isinstance(storm_arrival, dict) else None,
        "stormArrival": (storm_arrival or {}).get("arrivalEstimate") if isinstance(storm_arrival, dict) else None,
    }

    old = _LAST_ALERT_STATE.get(_key(place))
    _LAST_ALERT_STATE[_key(place)] = state

    if not old:
        return {
            "mode": "Watchman Alert Change Notifier V1",
            "changed": False,
            "firstScan": True,
            "changes": ["baseline created"],
            "state": state,
        }

    changes = []

    if state["alertCount"] != old.get("alertCount"):
        changes.append(f"alert count changed from {old.get('alertCount')} to {state['alertCount']}")

    old_ids = set(old.get("alertSignatures") or [])
    new_ids = set(state.get("alertSignatures") or [])

    added = new_ids - old_ids
    removed = old_ids - new_ids

    if added:
        changes.append(f"{len(added)} new alert signature(s)")
    if removed:
        changes.append(f"{len(removed)} alert signature(s) cleared")

    if state["threatScore"] != old.get("threatScore"):
        changes.append(f"threat score changed from {old.get('threatScore')} to {state['threatScore']}")

    if state["threatLevel"] != old.get("threatLevel"):
        changes.append(f"threat level changed from {old.get('threatLevel')} to {state['threatLevel']}")

    if state["stormStatus"] != old.get("stormStatus"):
        changes.append(f"storm status changed from {old.get('stormStatus')} to {state['stormStatus']}")

    if state["stormArrival"] != old.get("stormArrival"):
        changes.append(f"storm arrival changed from {old.get('stormArrival')} to {state['stormArrival']}")

    return {
        "mode": "Watchman Alert Change Notifier V1",
        "changed": bool(changes),
        "firstScan": False,
        "changes": changes or ["no alert/threat/storm notification change detected"],
        "state": state,
        "previous": old,
    }


def alert_change_summary():
    return {
        "mode": "Watchman Alert Change Notifier V1",
        "trackedPlaces": list(_LAST_ALERT_STATE.keys()),
        "states": _LAST_ALERT_STATE,
    }
