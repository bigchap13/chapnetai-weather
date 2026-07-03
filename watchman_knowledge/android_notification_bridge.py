import shutil
import subprocess
from datetime import datetime, timezone

_SENT_ANDROID = set()


def _now():
    return datetime.now(timezone.utc).isoformat()


def android_available():
    return shutil.which("termux-notification") is not None


def _priority(severity):
    severity = str(severity or "").lower()
    if severity in ["emergency", "urgent"]:
        return "high"
    return "default"


def send_android_notification(item):
    if not isinstance(item, dict):
        return {
            "sent": False,
            "reason": "invalid_delivery_item",
        }

    delivery_id = item.get("id")
    if delivery_id in _SENT_ANDROID:
        return {
            "sent": False,
            "reason": "already_sent",
            "deliveryId": delivery_id,
        }

    if not android_available():
        return {
            "sent": False,
            "reason": "termux_notification_not_available",
            "hint": "Install Termux:API app and package: pkg install termux-api",
            "deliveryId": delivery_id,
        }

    title = item.get("title") or "Watchman Alert"
    body = item.get("body") or ""
    severity = item.get("severity") or "info"

    cmd = [
        "termux-notification",
        "--id", str(delivery_id or 999),
        "--title", str(title),
        "--content", str(body),
        "--priority", _priority(severity),
    ]

    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as e:
        return {
            "sent": False,
            "reason": "termux_notification_failed",
            "error": str(e),
            "deliveryId": delivery_id,
        }

    if result.returncode == 0:
        _SENT_ANDROID.add(delivery_id)
        item["status"] = "sent_android"
        item["androidSentAt"] = _now()
        return {
            "sent": True,
            "deliveryId": delivery_id,
            "title": title,
            "severity": severity,
        }

    return {
        "sent": False,
        "reason": "termux_notification_nonzero_exit",
        "returncode": result.returncode,
        "stderr": result.stderr,
        "stdout": result.stdout,
        "deliveryId": delivery_id,
    }


def send_pending_android_notifications(deliveries):
    results = []
    for item in deliveries or []:
        if not isinstance(item, dict):
            continue
        if item.get("channel") != "phone_push_pending":
            continue
        if item.get("status") not in ["queued", "phone_push_pending"]:
            continue
        results.append(send_android_notification(item))

    return {
        "mode": "Watchman Android Notification Bridge",
        "available": android_available(),
        "attempted": len(results),
        "sent": len([r for r in results if r.get("sent")]),
        "results": results,
    }


def android_bridge_summary():
    return {
        "mode": "Watchman Android Notification Bridge",
        "available": android_available(),
        "sentCount": len(_SENT_ANDROID),
        "sentIds": sorted([x for x in _SENT_ANDROID if x is not None]),
        "hint": None if android_available() else "Install Termux:API app and run: pkg install termux-api",
    }
