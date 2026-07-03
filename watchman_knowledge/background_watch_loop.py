import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

WATCH_FILE = Path("data/watchman_watches.json")

_WATCHES = {}
_LOOP_STATE = {
    "running": False,
    "startedAt": None,
    "lastRun": None,
    "runs": 0,
    "intervalSeconds": 300,
}
_THREAD = None
_FLASK_APP = None


def set_flask_app(app):
    global _FLASK_APP
    _FLASK_APP = app


def _now():
    return datetime.now(timezone.utc).isoformat()


def _key(place):
    return str(place or "default").strip().lower()


def save_watches():
    WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_FILE.write_text(json.dumps({
        "savedAt": _now(),
        "watches": list(_WATCHES.values()),
    }, indent=2))
    return str(WATCH_FILE)


def load_persisted_watches():
    if not WATCH_FILE.exists():
        return {
            "loaded": 0,
            "path": str(WATCH_FILE),
        }

    try:
        data = json.loads(WATCH_FILE.read_text())
    except Exception:
        return {
            "loaded": 0,
            "path": str(WATCH_FILE),
            "error": "watch file could not be read",
        }

    rows = data.get("watches") or []
    loaded = 0

    for item in rows:
        if not isinstance(item, dict):
            continue
        place = item.get("place")
        if not place:
            continue

        item.setdefault("enabled", True)
        item.setdefault("checks", 0)
        item.setdefault("intervalSeconds", 300)
        _WATCHES[_key(place)] = item
        loaded += 1

    return {
        "loaded": loaded,
        "path": str(WATCH_FILE),
    }


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
    save_watches()
    return item


def unregister_watch(place):
    removed = _WATCHES.pop(_key(place), None)
    save_watches()
    return removed


def list_watches():
    return list(_WATCHES.values())


def background_watch_summary():
    return {
        "mode": "Watchman Background Watch Loop",
        "loop": dict(_LOOP_STATE),
        "watchCount": len(_WATCHES),
        "watchFile": str(WATCH_FILE),
        "watches": list_watches(),
    }


def _check_one_watch(watch):
    try:
        from flask import current_app
        from watchman_knowledge.radar_intelligence_v2 import radar_intelligence_v2
        from watchman_knowledge.storm_arrival_engine import storm_arrival_engine
        from watchman_knowledge.change_detection_engine import detect_weather_changes
        from watchman_knowledge.alert_change_notifier import alert_change_notifier
        from watchman_knowledge.emergency_mode import emergency_mode
        from watchman_knowledge.notification_engine import evaluate_notifications
        from watchman_knowledge.notification_delivery import queue_deliveries
        from watchman_knowledge.android_notification_bridge import send_pending_android_notifications

        place = watch.get("place")

        app_obj = _FLASK_APP
        if app_obj is None:
            app_obj = current_app._get_current_object()

        with app_obj.app_context():
            with app_obj.test_client() as client:
                resp = client.get("/api/nws", query_string={"place": place})
                weather = resp.get_json() or {}

        if "error" in weather:
            raise RuntimeError(str(weather.get("error")))

        radar_result = radar_intelligence_v2("background watch", weather)
        storm_arrival = storm_arrival_engine("background watch", weather)
        change_result = detect_weather_changes(place, weather, storm_arrival)
        alert_change = alert_change_notifier(place, weather, storm_arrival)
        emergency_result = emergency_mode("background watch", weather, radar_result)
        notify_result = evaluate_notifications(place, weather, emergency_result, radar_result)
        deliveries = queue_deliveries((notify_result or {}).get("created", []))
        send_pending_android_notifications(deliveries)

        watch["lastChecked"] = _now()
        watch["checks"] = int(watch.get("checks") or 0) + 1
        watch["lastStatus"] = {
            "ok": True,
            "createdNotifications": (notify_result or {}).get("createdCount", 0),
            "alertChange": alert_change,
            "weatherChange": change_result,
            "stormArrival": storm_arrival,
        }
        save_watches()
        return watch["lastStatus"]

    except Exception as e:
        watch["lastChecked"] = _now()
        watch["checks"] = int(watch.get("checks") or 0) + 1
        watch["lastStatus"] = {
            "ok": False,
            "error": str(e),
        }
        save_watches()
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
