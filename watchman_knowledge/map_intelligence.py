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


def _project_point(lat, lon, miles, bearing_deg):
    lat = _safe_float(lat)
    lon = _safe_float(lon)
    b = math.radians(_safe_float(bearing_deg))
    dlat = (miles * math.cos(b)) / 69.0
    dlon = (miles * math.sin(b)) / max(1, 69.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def _speed_from_threat(threat, storm):
    movement = str((storm or {}).get("movement") or "").lower()

    for token in movement.replace(",", " ").split():
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

    movement = storm.get("movement")
    bearing = _bearing_from_text(movement)
    speed_mph = _speed_from_threat(threat, storm)

    features = []

    features.append({
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
            "movement": movement,
            "bearingDegrees": bearing,
            "speedMph": speed_mph,
            "arrivalEstimate": arrival,
            "confidence": storm.get("confidence"),
            "color": color,
            "radiusMiles": radius,
            "projectionMinutes": 0,
            "note": "Proxy polygon generated from Watchman storm intelligence. Live radar cell contour extraction is the next phase.",
        },
    })

    for minutes, opacity_label in [(15, "projection_15"), (30, "projection_30"), (60, "projection_60")]:
        miles = speed_mph * (minutes / 60.0)
        plat, plon = _project_point(lat, lon, miles, bearing)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [_circle_polygon(plat, plon, max(6, radius - 4))],
            },
            "properties": {
                "kind": "watchman_storm_projection",
                "place": place,
                "title": f"Watchman Storm Projection +{minutes} min",
                "threatScore": threat,
                "precipChance": precip,
                "movement": movement,
                "bearingDegrees": bearing,
                "speedMph": speed_mph,
                "projectionMinutes": minutes,
                "arrivalEstimate": arrival,
                "confidence": storm.get("confidence"),
                "color": color,
                "radiusMiles": max(6, radius - 4),
                "note": "Projected polygon based on Watchman V1 direction/speed estimate.",
            },
        })

    return features


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
            "stormCellProxyPolygons": len([f for f in storm_features if (f.get("properties") or {}).get("kind") == "watchman_storm_cell_proxy"]),
            "stormProjectionPolygons": len([f for f in storm_features if (f.get("properties") or {}).get("kind") == "watchman_storm_projection"]),
            "total": len(alert_features) + len(storm_features),
        },
    }
