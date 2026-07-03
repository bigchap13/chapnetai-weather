from watchman_knowledge.notification_delivery import list_delivery_outbox

_ACKED = set()


def pending_phone_pushes(limit=20):
    rows = []
    for item in list_delivery_outbox(100):
        if item.get("channel") != "phone_push_pending":
            continue
        if item.get("id") in _ACKED:
            continue
        if item.get("status") != "queued":
            continue

        rows.append({
            "id": item.get("id"),
            "title": item.get("title") or "Watchman Alert",
            "body": item.get("body") or "",
            "severity": item.get("severity") or "info",
            "place": item.get("place"),
            "time": item.get("time"),
            "sourceNotificationId": item.get("sourceNotificationId"),
            "data": item.get("data") or {},
        })

    return rows[-limit:]


def acknowledge_phone_push(push_id=None):
    if push_id in [None, "", "all"]:
        rows = pending_phone_pushes(100)
        for item in rows:
            _ACKED.add(item.get("id"))
        return len(rows)

    try:
        push_id = int(push_id)
    except Exception:
        return 0

    _ACKED.add(push_id)
    return 1


def phone_push_summary():
    pending = pending_phone_pushes(100)
    urgent = [p for p in pending if p.get("severity") in ["urgent", "emergency"]]
    return {
        "mode": "Watchman Phone Push Bridge",
        "pending": len(pending),
        "urgentPending": len(urgent),
        "acked": len(_ACKED),
        "latest": pending[-1] if pending else None,
    }
