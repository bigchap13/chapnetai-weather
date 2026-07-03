from datetime import datetime, timezone

_GPS_WATCH_STATE = {
    "enabled": False,
    "lastUpdate": None,
    "lastGps": None,
    "lastResult": None,
    "updates": 0,
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def update_gps_watch(lat, lon, result=None, label="Phone GPS"):
    _GPS_WATCH_STATE["enabled"] = True
    _GPS_WATCH_STATE["lastUpdate"] = _now()
    _GPS_WATCH_STATE["lastGps"] = {
        "lat": lat,
        "lon": lon,
        "label": label,
    }
    _GPS_WATCH_STATE["lastResult"] = result
    _GPS_WATCH_STATE["updates"] += 1

    return gps_watch_summary()


def stop_gps_watch():
    _GPS_WATCH_STATE["enabled"] = False
    _GPS_WATCH_STATE["lastUpdate"] = _now()
    return gps_watch_summary()


def gps_watch_summary():
    return {
        "mode": "Watchman Continuous GPS Watch V1",
        "enabled": _GPS_WATCH_STATE["enabled"],
        "lastUpdate": _GPS_WATCH_STATE["lastUpdate"],
        "lastGps": _GPS_WATCH_STATE["lastGps"],
        "lastResult": _GPS_WATCH_STATE["lastResult"],
        "updates": _GPS_WATCH_STATE["updates"],
        "note": "V1 stores live phone GPS impact updates in memory. Persistence and background server-side polling are next.",
    }
