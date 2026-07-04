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


def _circle_polygon(lat, lon, radius_miles=15, points=36):
    lat = _safe_float(lat)
    lon = _safe_float(lon)
    coords = []

    for i in range(points + 1):
        angle = 2 * math.pi * i / points
        dlat = (radius_miles / 69.0) * math.sin(angle)
        dlon = (radius_miles / max(1, 69.0 * math.cos(math.radians(lat)))) * math.cos(angle)
        coords.append([lon + dlon, lat + dlat])

    return coords


def _classify_alert(event):
    e = str(event or "").lower()

    if "tornado warning" in e:
        return "tornado_warning", "warning", "#ff0000", 0.32, True
    if "tornado watch" in e:
        return "tornado_watch", "watch", "#ff4d4d", 0.18, False
    if "severe thunderstorm warning" in e:
        return "severe_thunderstorm_warning", "warning", "#ff9800", 0.28, True
    if "severe thunderstorm watch" in e:
        return "severe_thunderstorm_watch", "watch", "#ffb74d", 0.16, False
    if "flash flood warning" in e:
        return "flash_flood_warning", "warning", "#00c853", 0.28, True
    if "flood" in e:
        return "flood", "flood", "#00e676", 0.18, False
    if "heat" in e:
        return "heat", "advisory", "#e040fb", 0.18, False
    if "winter" in e or "snow" in e or "ice" in e:
        return "winter", "warning", "#40c4ff", 0.22, True
    if "special weather statement" in e:
        return "special_weather_statement", "statement", "#ffd600", 0.14, False
    if "advisory" in e:
        return "advisory", "advisory", "#ffd600", 0.14, False
    if "watch" in e:
        return "watch", "watch", "#ffcc00", 0.14, False
    if "warning" in e:
        return "warning", "warning", "#ff5252", 0.24, True

    return "other", "other", "#ffd600", 0.12, False


def _alert_id(props):
    for key in ["id", "@id", "identifier", "eventId", "capId"]:
        v = props.get(key)
        if v:
            return str(v)

    return "|".join([
        str(props.get("event") or ""),
        str(props.get("headline") or ""),
        str(props.get("areaDesc") or ""),
        str(props.get("effective") or ""),
        str(props.get("expires") or ""),
    ])


def build_advanced_nws_polygon_layer(place, lat, lon):
    url = f"https://api.weather.gov/alerts/active?point={float(lat):.4f},{float(lon):.4f}"
    headers = {"User-Agent": "CHAPNetAI-Watchman/1.0"}

    data = requests.get(url, headers=headers, timeout=12).json()

    features = []
    counts = {
        "total": 0,
        "official": 0,
        "fallback": 0,
        "warnings": 0,
        "watches": 0,
        "advisories": 0,
        "flood": 0,
        "statements": 0,
        "other": 0,
    }

    for item in data.get("features") or []:
        props = item.get("properties") or {}
        geom = item.get("geometry")
        event = props.get("event") or "Weather Alert"
        alert_type, layer_group, color, fill_opacity, flashing = _classify_alert(event)

        fallback = False
        if not geom:
            fallback = True
            geom = {
                "type": "Polygon",
                "coordinates": [_circle_polygon(lat, lon, 18)],
            }

        if layer_group == "warning":
            counts["warnings"] += 1
        elif layer_group == "watch":
            counts["watches"] += 1
        elif layer_group == "advisory":
            counts["advisories"] += 1
        elif layer_group == "flood":
            counts["flood"] += 1
        elif layer_group == "statement":
            counts["statements"] += 1
        else:
            counts["other"] += 1

        counts["total"] += 1
        counts["fallback" if fallback else "official"] += 1

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "kind": "advanced_nws_polygon",
                "place": place,
                "alertId": _alert_id(props),
                "event": event,
                "alertType": alert_type,
                "layerGroup": layer_group,
                "headline": props.get("headline"),
                "description": props.get("description"),
                "instruction": props.get("instruction"),
                "areaDesc": props.get("areaDesc"),
                "severity": props.get("severity"),
                "urgency": props.get("urgency"),
                "certainty": props.get("certainty"),
                "sender": props.get("senderName"),
                "effective": props.get("effective"),
                "expires": props.get("expires"),
                "color": color,
                "fillOpacity": fill_opacity,
                "flashing": flashing,
                "fallback": fallback,
            },
        })

    return {
        "mode": "Watchman Advanced NWS Polygon Layer V1",
        "time": _now(),
        "place": place,
        "center": {"lat": lat, "lon": lon},
        "counts": counts,
        "features": features,
        "source": url,
        "note": "Advanced polygon layer separates watches, warnings, advisories, flood areas, statements, official geometries, and fallback polygons.",
    }
