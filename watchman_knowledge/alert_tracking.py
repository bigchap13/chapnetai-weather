from datetime import datetime, timezone

_SEEN_ALERT_IDS = set()
_ALERT_HISTORY = []


def _now():
    return datetime.now(timezone.utc).isoformat()


def _alert_id(alert):
    if not isinstance(alert, dict):
        return None

    for key in ["id", "@id", "identifier", "eventId", "capId"]:
        value = alert.get(key)
        if value:
            return str(value)

    parts = [
        str(alert.get("event", "")),
        str(alert.get("headline", "")),
        str(alert.get("areaDesc", "")),
        str(alert.get("effective", "")),
        str(alert.get("expires", "")),
    ]
    fallback = "|".join(parts).strip("|")
    return fallback or None


def track_alerts(place, weather):
    weather = weather or {}
    alerts = weather.get("alerts") or []

    new_alerts = []
    active_ids = []

    for alert in alerts:
        aid = _alert_id(alert)
        if not aid:
            continue

        active_ids.append(aid)

        if aid not in _SEEN_ALERT_IDS:
            _SEEN_ALERT_IDS.add(aid)
            new_alerts.append(alert)
            _ALERT_HISTORY.append({
                "time": _now(),
                "place": place,
                "alertId": aid,
                "event": alert.get("event"),
                "headline": alert.get("headline"),
                "areaDesc": alert.get("areaDesc"),
            })

    _ALERT_HISTORY[:] = _ALERT_HISTORY[-200:]

    return {
        "mode": "Watchman Alert Tracking",
        "place": place,
        "activeAlertCount": len(alerts),
        "newAlertCount": len(new_alerts),
        "newAlerts": new_alerts,
        "activeAlertIds": active_ids,
        "seenAlertCount": len(_SEEN_ALERT_IDS),
        "history": _ALERT_HISTORY[-20:],
    }


def alert_tracking_summary():
    return {
        "mode": "Watchman Alert Tracking",
        "seenAlertCount": len(_SEEN_ALERT_IDS),
        "history": _ALERT_HISTORY[-20:],
    }
