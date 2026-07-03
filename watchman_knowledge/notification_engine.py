from datetime import datetime, timezone

_NOTIFICATIONS = []
_LAST_SIGNATURES = {}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _sig(kind, place, data):
    data = data or {}
    parts = [
        str(kind),
        str(place or "selected_location").lower(),
        str(data.get("alertCount", "")),
        str(data.get("threatScore", "")),
        str(data.get("threatLevel", "")),
    ]

    radar = data.get("radar") if isinstance(data.get("radar"), dict) else {}
    emergency = data.get("emergency") if isinstance(data.get("emergency"), dict) else {}

    parts.extend([
        str(radar.get("verdict", "")),
        str(radar.get("score", "")),
        str(radar.get("arrivalEstimate", "")),
        str(emergency.get("active", "")),
        str(emergency.get("event", "")),
        str(emergency.get("level", "")),
    ])

    return "|".join(parts)


def add_notification(kind, title, message, severity="info", place=None, data=None, dedupe=True):
    signature = _sig(kind, place, data or {})
    key = f"{kind}:{str(place or 'selected_location').lower()}"

    if dedupe and _LAST_SIGNATURES.get(key) == signature:
        return None

    _LAST_SIGNATURES[key] = signature

    item = {
        "id": len(_NOTIFICATIONS) + 1,
        "time": _now(),
        "kind": kind,
        "severity": severity,
        "title": title,
        "message": message,
        "place": place,
        "read": False,
        "signature": signature,
        "data": data or {},
    }

    _NOTIFICATIONS.append(item)
    _NOTIFICATIONS[:] = _NOTIFICATIONS[-100:]
    return item


def list_notifications(unread_only=False, limit=25):
    rows = [n for n in _NOTIFICATIONS if (not unread_only or not n.get("read"))]
    return rows[-limit:]


def mark_all_read():
    for n in _NOTIFICATIONS:
        n["read"] = True
    return len(_NOTIFICATIONS)


def notification_summary():
    unread = [n for n in _NOTIFICATIONS if not n.get("read")]
    urgent = [n for n in unread if n.get("severity") in ["urgent", "emergency"]]
    return {
        "mode": "Watchman Notification Engine",
        "total": len(_NOTIFICATIONS),
        "unread": len(unread),
        "urgentUnread": len(urgent),
        "latest": _NOTIFICATIONS[-1] if _NOTIFICATIONS else None,
    }


def evaluate_notifications(place, weather, emergency_result=None, radar_result=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []

    created = []

    threat_score = _safe_int(watchman.get("threatScore"), 0)
    threat_level = str(watchman.get("threatLevel") or "unknown")

    if isinstance(emergency_result, dict) and emergency_result.get("active"):
        item = add_notification(
            "emergency",
            "Watchman Emergency Mode Active",
            emergency_result.get("answer", "Emergency Mode activated."),
            "emergency",
            place,
            {"emergency": emergency_result},
        )
        if item:
            created.append(item)

    elif alerts:
        item = add_notification(
            "alert",
            f"{len(alerts)} active weather alert(s)",
            f"Watchman sees {len(alerts)} active alert(s) for {place or 'selected location'}.",
            "urgent" if threat_score >= 50 else "warning",
            place,
            {"alertCount": len(alerts), "threatScore": threat_score},
        )
        if item:
            created.append(item)

    if threat_score >= 50:
        item = add_notification(
            "threat_score",
            f"Watchman threat level {threat_level}",
            f"Threat score is {threat_score}/100 for {place or 'selected location'}.",
            "urgent",
            place,
            {"threatLevel": threat_level, "threatScore": threat_score},
        )
        if item:
            created.append(item)

    if isinstance(radar_result, dict):
        radar_score = _safe_int(radar_result.get("score"), 0)
        if radar_score >= 75:
            item = add_notification(
                "radar",
                "Radar risk elevated",
                radar_result.get("answer", "Radar Intelligence detected elevated storm risk."),
                "urgent",
                place,
                {"radar": radar_result},
            )
            if item:
                created.append(item)

    return {
        "mode": "Watchman Notification Engine",
        "created": created,
        "createdCount": len(created),
        "summary": notification_summary(),
    }


def notification_answer(question):
    q = str(question or "").lower()

    if not any(x in q for x in [
        "notification",
        "notifications",
        "alerts inbox",
        "watchman inbox",
        "unread alerts",
        "mark notifications read",
        "clear notifications",
    ]):
        return None

    if "mark" in q and "read" in q:
        count = mark_all_read()
        return {
            "mode": "Watchman Notification Engine",
            "answer": f"Marked {count} Watchman notification(s) as read.",
            "summary": notification_summary(),
        }

    rows = list_notifications(unread_only=("unread" in q), limit=10)
    if not rows:
        return {
            "mode": "Watchman Notification Engine",
            "answer": "No Watchman notifications are currently stored in this server session.",
            "summary": notification_summary(),
        }

    latest = rows[-1]
    return {
        "mode": "Watchman Notification Engine",
        "answer": (
            f"Watchman has {len(rows)} notification(s) in this view. "
            f"Latest: {latest.get('title')}: {latest.get('message')}"
        ),
        "notifications": rows,
        "summary": notification_summary(),
    }
