import math
import requests


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


def _circle_polygon(lat, lon, radius_miles=10, points=36):
    lat = _safe_float(lat)
    lon = _safe_float(lon)
    radius_deg_lat = radius_miles / 69.0
    coords = []

    for i in range(points + 1):
        angle = 2 * math.pi * i / points
        dlat = radius_deg_lat * math.sin(angle)
        dlon = (radius_miles / max(1, 69.0 * math.cos(math.radians(lat)))) * math.cos(angle)
        coords.append([lon + dlon, lat + dlat])

    return coords


def _alert_color(event):
    event = str(event or "").lower()
    if "tornado" in event:
        return "#ff2b2b"
    if "severe thunderstorm" in event:
        return "#ff9800"
    if "flash flood" in event or "flood" in event:
        return "#00c853"
    if "heat" in event:
        return "#e040fb"
    if "winter" in event or "ice" in event or "snow" in event:
        return "#40c4ff"
    return "#ffd600"


def nws_alert_polygon_features(lat, lon):
    url = f"https://api.weather.gov/alerts/active?point={float(lat):.4f},{float(lon):.4f}"
    headers = {"User-Agent": "CHAPNetAI-Watchman/1.0"}
    data = requests.get(url, headers=headers, timeout=12).json()

    features = []
    for item in data.get("features") or []:
        props = item.get("properties") or {}
        geom = item.get("geometry")

        event = props.get("event") or "Weather Alert"

        if not geom:
            geom = {
                "type": "Polygon",
                "coordinates": [_circle_polygon(lat, lon, 18)],
            }
            polygon_kind = "nws_alert_fallback_polygon"
            fallback = True
        else:
            polygon_kind = "nws_alert_polygon"
            fallback = False

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "kind": polygon_kind,
                "fallback": fallback,
                "event": event,
                "headline": props.get("headline"),
                "areaDesc": props.get("areaDesc"),
                "severity": props.get("severity"),
                "urgency": props.get("urgency"),
                "certainty": props.get("certainty"),
                "effective": props.get("effective"),
                "expires": props.get("expires"),
                "color": _alert_color(event),
            },
        })

    return features


def storm_cell_proxy_features(place, lat, lon, weather, storm_arrival=None):
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

    if not storm_signal:
        return []

    if threat >= 75:
        radius = 24
        color = "#ff2b2b"
    elif threat >= 50:
        radius = 18
        color = "#ff9800"
    else:
        radius = 12
        color = "#ffd600"

    arrival = (storm_arrival or {}).get("arrivalEstimate") if isinstance(storm_arrival, dict) else storm.get("estimatedArrival")

    return [{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [_circle_polygon(lat, lon, radius)],
        },
        "properties": {
            "kind": "watchman_storm_cell_proxy",
            "place": place,
            "title": "Watchman Storm Cell Proxy",
            "threatScore": threat,
            "precipChance": precip,
            "nearestStorm": storm.get("nearestStorm"),
            "intensity": storm.get("intensity"),
            "movement": storm.get("movement"),
            "arrivalEstimate": arrival,
            "confidence": storm.get("confidence"),
            "color": color,
            "radiusMiles": radius,
            "note": "Proxy polygon generated from Watchman storm intelligence. Live radar cell contour extraction is the next phase.",
        },
    }]


def build_map_intelligence(place, lat, lon, weather, storm_arrival=None):
    alert_features = nws_alert_polygon_features(lat, lon)
    storm_features = storm_cell_proxy_features(place, lat, lon, weather, storm_arrival)

    return {
        "mode": "Watchman Radar Map Intelligence V1",
        "place": place,
        "center": {"lat": lat, "lon": lon},
        "features": alert_features + storm_features,
        "counts": {
            "nwsAlertPolygons": len([f for f in alert_features if (f.get("properties") or {}).get("kind") == "nws_alert_polygon"]),
            "nwsAlertFallbackPolygons": len([f for f in alert_features if (f.get("properties") or {}).get("kind") == "nws_alert_fallback_polygon"]),
            "stormCellProxyPolygons": len(storm_features),
            "total": len(alert_features) + len(storm_features),
        },
    }
