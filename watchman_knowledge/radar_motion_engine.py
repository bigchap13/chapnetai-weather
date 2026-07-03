import math
import requests
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def _bearing_from_text(text):
    text = str(text or "").lower()

    if "from the west" in text or "moving east" in text:
        return 90
    if "from the east" in text or "moving west" in text:
        return 270
    if "from the south" in text or "moving north" in text:
        return 0
    if "from the north" in text or "moving south" in text:
        return 180
    if "northeast" in text:
        return 45
    if "southeast" in text:
        return 135
    if "southwest" in text:
        return 225
    if "northwest" in text:
        return 315

    return 270


def _speed_from_watchman(threat, storm):
    movement = str((storm or {}).get("movement") or "").lower()

    for token in movement.replace(",", " ").replace("mph", " mph").split():
        try:
            value = int(token)
            if 5 <= value <= 90:
                return value
        except Exception:
            pass

    if threat >= 75:
        return 45
    if threat >= 50:
        return 35
    return 25


def _project_point(lat, lon, miles, bearing_deg):
    lat = _safe_float(lat)
    lon = _safe_float(lon)
    b = math.radians(_safe_float(bearing_deg))
    dlat = (miles * math.cos(b)) / 69.0
    dlon = (miles * math.sin(b)) / max(1, 69.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def _rainviewer_frames():
    try:
        data = requests.get(
            "https://api.rainviewer.com/public/weather-maps.json",
            timeout=10,
        ).json()
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "frames": [],
        }

    past = ((data.get("radar") or {}).get("past") or [])[-6:]
    nowcast = ((data.get("radar") or {}).get("nowcast") or [])[:3]

    return {
        "ok": True,
        "generated": data.get("generated"),
        "host": data.get("host"),
        "frames": past + nowcast,
        "pastCount": len(past),
        "nowcastCount": len(nowcast),
    }


def radar_motion_engine(place, lat, lon, weather, storm_arrival=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}

    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)

    storm_signal = (
        storm.get("nearestStorm") == "Detected"
        or intel.get("stormSignal") == "detected"
        or threat >= 50
        or precip >= 35
    )

    movement = storm.get("movement")
    bearing = _bearing_from_text(movement)
    speed = _speed_from_watchman(threat, storm)

    projections = []
    for minutes in [15, 30, 60]:
        miles = speed * (minutes / 60.0)
        plat, plon = _project_point(lat, lon, miles, bearing)
        projections.append({
            "minutes": minutes,
            "miles": round(miles, 2),
            "lat": round(plat, 5),
            "lon": round(plon, 5),
        })

    frames = _rainviewer_frames()

    confidence = 55
    if frames.get("ok"):
        confidence += 10
    if storm_signal:
        confidence += 15
    if threat >= 50:
        confidence += 10

    confidence = min(confidence, 85)

    return {
        "mode": "Watchman Radar Motion Engine V1",
        "time": _now(),
        "place": place,
        "center": {
            "lat": lat,
            "lon": lon,
        },
        "stormSignal": storm_signal,
        "bearingDegrees": bearing,
        "speedMph": speed,
        "movementSource": movement or "Watchman fallback estimate",
        "arrivalEstimate": (storm_arrival or {}).get("arrivalEstimate") if isinstance(storm_arrival, dict) else None,
        "threatScore": threat,
        "precipChance": precip,
        "confidence": confidence,
        "projections": projections,
        "rainviewer": frames,
        "answer": (
            f"Radar Motion Engine V1: storm signal {'active' if storm_signal else 'not strong'}. "
            f"Estimated movement bearing {bearing} degrees at {speed} mph. "
            f"Projection points created for 15, 30, and 60 minutes. "
            f"Confidence: {confidence}%."
        ),
        "note": "V1 uses RainViewer frame availability plus Watchman movement estimation. True pixel-level storm-cell contour tracking is the next hard phase.",
    }
