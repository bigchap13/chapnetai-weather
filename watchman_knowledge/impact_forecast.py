import math
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


def _distance_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _project_point(lat, lon, miles, bearing_deg):
    lat = _safe_float(lat)
    lon = _safe_float(lon)
    b = math.radians(_safe_float(bearing_deg))
    dlat = (miles * math.cos(b)) / 69.0
    dlon = (miles * math.sin(b)) / max(1, 69.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


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


def _impact_level(distance, threat, confidence):
    if distance <= 5 and threat >= 50:
        return "high"
    if distance <= 8 and confidence >= 70:
        return "elevated"
    if distance <= 15:
        return "possible"
    return "low"


def _recommendation(level, minutes):
    if level == "high":
        return f"Likely impact within about {minutes} minutes. Stay indoors and keep Watchman open."
    if level == "elevated":
        return f"Storm path may affect this area within about {minutes} minutes. Prepare for quick weather changes."
    if level == "possible":
        return f"Possible nearby impact within about {minutes} minutes. Monitor radar and alerts."
    return f"No strong impact signal for the +{minutes} minute window."


def impact_forecast(place, lat, lon, weather, multi_cell=None):
    lat = _safe_float(lat)
    lon = _safe_float(lon)
    weather = weather or {}
    watchman = weather.get("watchman") or {}

    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)
    alerts = weather.get("alerts") or []

    tracks = []
    if isinstance(multi_cell, dict):
        tracks = multi_cell.get("tracks") or []

    tracked = [t for t in tracks if t.get("status") == "tracked"]

    impacts = []
    features = []

    for t in tracked[:8]:
        cur = t.get("current") or {}
        speed = _safe_float(t.get("speedMph"), 0)
        bearing = _safe_float(t.get("bearingDegrees"), 270)
        confidence = _safe_int(t.get("confidence"), 50)

        for minutes in [15, 30, 60]:
            miles = speed * (minutes / 60.0)
            plat, plon = _project_point(cur.get("lat"), cur.get("lon"), miles, bearing)
            distance = _distance_miles(lat, lon, plat, plon)
            level = _impact_level(distance, threat, confidence)

            item = {
                "cellId": t.get("cellId"),
                "minutes": minutes,
                "projectedLat": round(plat, 5),
                "projectedLon": round(plon, 5),
                "distanceFromPlaceMiles": round(distance, 2),
                "impactLevel": level,
                "confidence": confidence,
                "speedMph": speed,
                "bearingDegrees": bearing,
                "strengthTrend": t.get("strengthTrend"),
                "recommendation": _recommendation(level, minutes),
            }
            impacts.append(item)

            if level != "low":
                color = "#ff2b2b" if level == "high" else "#ff9800" if level == "elevated" else "#ffd600"
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [_circle_polygon(plat, plon, 8 if level == "high" else 6)],
                    },
                    "properties": {
                        "kind": "watchman_impact_forecast_zone",
                        "place": place,
                        "cellId": t.get("cellId"),
                        "title": f"Impact Forecast {t.get('cellId')} +{minutes} min",
                        "impactLevel": level,
                        "projectionMinutes": minutes,
                        "distanceFromPlaceMiles": round(distance, 2),
                        "confidence": confidence,
                        "speedMph": speed,
                        "bearingDegrees": bearing,
                        "strengthTrend": t.get("strengthTrend"),
                        "color": color,
                        "recommendation": _recommendation(level, minutes),
                    },
                })

    impacts.sort(key=lambda x: (
        {"high": 0, "elevated": 1, "possible": 2, "low": 3}.get(x["impactLevel"], 9),
        x["minutes"],
        x["distanceFromPlaceMiles"],
    ))

    highest = impacts[0]["impactLevel"] if impacts else "unknown"

    if not tracked:
        answer = f"Impact Forecast V1: no tracked radar cells available near {place}."
    else:
        answer = f"Impact Forecast V1: highest projected impact for {place} is {highest}. {len(features)} impact zone(s) created."

    return {
        "mode": "Watchman Impact Forecast V1",
        "time": _now(),
        "place": place,
        "center": {"lat": lat, "lon": lon},
        "trackedCells": len(tracked),
        "alertCount": len(alerts),
        "threatScore": threat,
        "precipChance": precip,
        "highestImpact": highest,
        "impactCount": len(impacts),
        "featureCount": len(features),
        "impacts": impacts,
        "features": features,
        "answer": answer,
        "note": "V1 projects tracked radar cells into 15/30/60 minute impact windows near the selected place.",
    }
