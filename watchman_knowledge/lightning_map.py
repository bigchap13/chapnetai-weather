import math
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def _safe_float(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d


def _circle_polygon(lat, lon, radius_miles=8, points=36):
    lat = _safe_float(lat)
    lon = _safe_float(lon)
    coords = []

    for i in range(points + 1):
        angle = 2 * math.pi * i / points
        dlat = (radius_miles / 69.0) * math.sin(angle)
        dlon = (radius_miles / max(1, 69.0 * math.cos(math.radians(lat)))) * math.cos(angle)
        coords.append([lon + dlon, lat + dlat])

    return coords


def _project_point(lat, lon, miles, bearing_deg):
    b = math.radians(_safe_float(bearing_deg))
    dlat = (miles * math.cos(b)) / 69.0
    dlon = (miles * math.sin(b)) / max(1, 69.0 * math.cos(math.radians(_safe_float(lat))))
    return _safe_float(lat) + dlat, _safe_float(lon) + dlon


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


def lightning_intelligence(place, lat, lon, weather, radar_motion=None, radar_cell=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}
    alerts = weather.get("alerts") or []

    text = " ".join([
        str(storm.get("conditions") or ""),
        str(storm.get("intensity") or ""),
        str(storm.get("forecastWindow") or ""),
        str(intel.get("nextWindow") or ""),
        " ".join(str(a.get("event") or "") + " " + str(a.get("headline") or "") for a in alerts if isinstance(a, dict)),
    ]).lower()

    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)

    thunder_signal = (
        "thunder" in text
        or "lightning" in text
        or storm.get("nearestStorm") == "Detected"
        or intel.get("stormSignal") == "detected"
    )

    if thunder_signal and threat >= 50:
        risk = "high"
        score = 85
        radius = 18
        color = "#ff2b2b"
    elif thunder_signal or threat >= 35 or precip >= 45:
        risk = "elevated"
        score = 65
        radius = 12
        color = "#ff9800"
    elif precip >= 25:
        risk = "watch"
        score = 40
        radius = 8
        color = "#ffd600"
    else:
        risk = "low"
        score = 15
        radius = 0
        color = "#8bc34a"

    motion = radar_motion or {}
    cell = (radar_cell or {}).get("cell") if isinstance(radar_cell, dict) else {}

    bearing = (
        cell.get("bearingDegrees")
        if isinstance(cell, dict) and cell.get("bearingDegrees") is not None
        else motion.get("bearingDegrees")
        if isinstance(motion, dict) and motion.get("bearingDegrees") is not None
        else _bearing_from_text(storm.get("movement"))
    )

    speed = (
        cell.get("speedMph")
        if isinstance(cell, dict) and cell.get("speedMph") is not None
        else motion.get("speedMph")
        if isinstance(motion, dict) and motion.get("speedMph") is not None
        else 25
    )

    features = []

    if risk != "low":
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [_circle_polygon(lat, lon, radius)],
            },
            "properties": {
                "kind": "watchman_lightning_risk_zone",
                "title": "Watchman Lightning Risk Zone",
                "place": place,
                "risk": risk,
                "score": score,
                "radiusMiles": radius,
                "bearingDegrees": bearing,
                "speedMph": speed,
                "color": color,
                "note": "V1 lightning layer uses Watchman storm/thunder signals, alerts, precipitation, and radar motion. Real strike-feed ingestion is a future layer.",
            },
        })

        for minutes in [15, 30]:
            miles = _safe_float(speed) * (minutes / 60.0)
            plat, plon = _project_point(lat, lon, miles, bearing)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [_circle_polygon(plat, plon, max(5, radius - 3))],
                },
                "properties": {
                    "kind": "watchman_lightning_projection_zone",
                    "title": f"Watchman Lightning Projection +{minutes} min",
                    "place": place,
                    "risk": risk,
                    "score": score,
                    "projectionMinutes": minutes,
                    "bearingDegrees": bearing,
                    "speedMph": speed,
                    "color": color,
                    "note": "Projected lightning-risk zone based on radar/storm motion estimate.",
                },
            })

    return {
        "mode": "Watchman Lightning Intelligence Layer V1",
        "time": _now(),
        "place": place,
        "center": {"lat": lat, "lon": lon},
        "risk": risk,
        "score": score,
        "thunderSignal": thunder_signal,
        "threatScore": threat,
        "precipChance": precip,
        "bearingDegrees": bearing,
        "speedMph": speed,
        "featureCount": len(features),
        "features": features,
        "answer": f"Lightning Intelligence V1: {risk} lightning risk near {place}. Score {score}/100.",
        "note": "This is lightning-risk intelligence, not a live strike feed. Real lightning strike data is the next upgrade.",
    }
