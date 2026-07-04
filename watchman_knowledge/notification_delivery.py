from datetime import datetime, timezone

from watchman_knowledge.smart_notification_text import build_smart_notification_text

_DELIVERY_OUTBOX = []


def _now():
    return datetime.now(timezone.utc).isoformat()


def queue_delivery(notification):
    if not isinstance(notification, dict):
        return None

    smart_title, smart_body = build_smart_notification_text(notification)

    item = {
        "id": len(_DELIVERY_OUTBOX) + 1,
        "time": _now(),
        "channel": "phone_push_pending",
        "status": "queued",
        "title": smart_title,
        "body": smart_body,
        "severity": notification.get("severity") or "info",
        "place": notification.get("place"),
        "sourceNotificationId": notification.get("id"),
        "data": notification,
    }

    _DELIVERY_OUTBOX.append(item)
    _DELIVERY_OUTBOX[:] = _DELIVERY_OUTBOX[-100:]
    return item


def queue_deliveries(notifications):
    created = []
    for n in notifications or []:
        item = queue_delivery(n)
        if item:
            created.append(item)
    return created


def list_delivery_outbox(limit=50):
    return _DELIVERY_OUTBOX[-limit:]


def delivery_summary():
    queued = [x for x in _DELIVERY_OUTBOX if x.get("status") == "queued"]
    return {
        "mode": "Watchman Notification Delivery",
        "total": len(_DELIVERY_OUTBOX),
        "queued": len(queued),
        "latest": _DELIVERY_OUTBOX[-1] if _DELIVERY_OUTBOX else None,
    }
