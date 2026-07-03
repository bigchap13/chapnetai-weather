import threading
import time
from datetime import datetime, timezone

_WATCHES = {}
_LOOP_STATE = {
    "running": False,
    "startedAt": None,
    "lastRun": None,
    "runs": 0,
    "intervalSeconds": 300,
}
_THREAD = None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _key(place):
    return str(place or "default").strip().lower()


def register_watch(place, label=None, interval_seconds=300):
    place = place or "default"
    item = {
        "place": place,
        "label": label or place,
        "createdAt": _now(),
        "intervalSeconds": int(interval_seconds or 300),
        "lastChecked": None,
        "checks": 0,
        "enabled": True,
    }
    _WATCHES[_key(place)] = item
    return item


def unregister_watch(place):
    return _WATCHES.pop(_key(place), None)


def list_watches():
    return list(_WATCHES.values())


def background_watch_summary():
    return {
        "mode": "Watchman Background Watch Loop",
        "loop": dict(_LOOP_STATE),
        "watchCount": len(_WATCHES),
        "watches": list_watches(),
    }


def _check_one_watch(watch):
    try:
        # Import here to avoid circular imports during app startup.
        from app import get_weather_for_place
        from watchman_knowledge.radar_intelligence_v2 import radar_intelligence_v2
        from watchman_knowledge.emergency_mode import emergency_mode
        from watchman_knowledge.notification_engine import evaluate_notifications
        from watchman_knowledge.notification_delivery import queue_deliveries
        from watchman_knowledge.android_notification_bridge import send_pending_android_notifications

        place = watch.get("place")
        weather = get_weather_for_place(place)

        radar_result = radar_intelligence_v2("background watch", weather)
        emergency_result = emergency_mode("background watch", weather, radar_result)
        notify_result = evaluate_notifications(place, weather, emergency_result, radar_result)
        deliveries = queue_deliveries((notify_result or {}).get("created", []))
        send_pending_android_notifications(deliveries)

        watch["lastChecked"] = _now()
        watch["checks"] = int(watch.get("checks") or 0) + 1
        watch["lastStatus"] = {
            "ok": True,
            "createdNotifications": (notify_result or {}).get("createdCount", 0),
        }
        return watch["lastStatus"]

    except Exception as e:
        watch["lastChecked"] = _now()
        watch["checks"] = int(watch.get("checks") or 0) + 1
        watch["lastStatus"] = {
            "ok": False,
            "error": str(e),
        }
        return watch["lastStatus"]


def run_watch_once():
    results = []
    for watch in list(_WATCHES.values()):
        if not watch.get("enabled"):
            continue
        results.append({
            "place": watch.get("place"),
            "result": _check_one_watch(watch),
        })

    _LOOP_STATE["lastRun"] = _now()
    _LOOP_STATE["runs"] = int(_LOOP_STATE.get("runs") or 0) + 1

    return {
        "mode": "Watchman Background Watch Loop",
        "ran": len(results),
        "results": results,
        "summary": background_watch_summary(),
    }


def _loop():
    while _LOOP_STATE.get("running"):
        run_watch_once()
        time.sleep(int(_LOOP_STATE.get("intervalSeconds") or 300))


def start_background_watch_loop(interval_seconds=300):
    global _THREAD

    _LOOP_STATE["intervalSeconds"] = int(interval_seconds or 300)

    if _LOOP_STATE.get("running"):
        return background_watch_summary()

    _LOOP_STATE["running"] = True
    _LOOP_STATE["startedAt"] = _now()

    _THREAD = threading.Thread(target=_loop, daemon=True)
    _THREAD.start()

    return background_watch_summary()


def stop_background_watch_loop():
    _LOOP_STATE["running"] = False
    return background_watch_summary()
