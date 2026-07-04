from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from watchman_knowledge.weather_service import weather_lookup_for_gps, weather_lookup_for_place


def _num(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _text(v: Any) -> str:
    return str(v or "").strip()


def _dig(obj: Any, keys: List[str]) -> Any:
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _find_lat_lon(obj: Any) -> Tuple[Optional[float], Optional[float]]:
    if not isinstance(obj, dict):
        return None, None

    candidates = [
        ("lat", "lon"),
        ("latitude", "longitude"),
        ("Lat", "Lon"),
    ]

    for a, b in candidates:
        lat = _num(obj.get(a))
        lon = _num(obj.get(b))
        if lat is not None and lon is not None:
            return lat, lon

    nested_paths = [
        ["location"],
        ["geo"],
        ["coordinates"],
        ["point"],
        ["place"],
    ]

    for path in nested_paths:
        child = _dig(obj, path)
        lat, lon = _find_lat_lon(child)
        if lat is not None and lon is not None:
            return lat, lon

    return None, None


def _geocode_destination(destination: str) -> Dict[str, Any]:
    import json
    import urllib.parse
    import urllib.request

    q = urllib.parse.urlencode({"format": "json", "limit": "1", "q": destination})
    url = "https://nominatim.openstreetmap.org/search?" + q

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ChapNetAI-Watchman-Route-Planner/1.0"
        },
    )

    with urllib.request.urlopen(req, timeout=12) as res:
        data = json.loads(res.read().decode("utf-8"))

    if not data:
        return {"ok": False, "error": "destination_not_found", "destination": destination}

    hit = data[0]
    lat = _num(hit.get("lat"))
    lon = _num(hit.get("lon"))

    if lat is None or lon is None:
        return {"ok": False, "error": "destination_coordinates_not_found", "destination": destination}

    return {
        "ok": True,
        "destination": destination,
        "lat": lat,
        "lon": lon,
        "displayName": hit.get("display_name") or destination,
        "source": "openstreetmap_nominatim",
    }


def _destination_to_gps(destination: str) -> Dict[str, Any]:
    destination = _text(destination)
    if not destination:
        return {"ok": False, "error": "destination_required"}

    weather = None

    try:
        weather = weather_lookup_for_place(destination)
        lat, lon = _find_lat_lon(weather)
        if lat is not None and lon is not None:
            return {
                "ok": True,
                "destination": destination,
                "lat": lat,
                "lon": lon,
                "weather": weather,
                "source": "weather_lookup_for_place",
            }
    except Exception:
        pass

    try:
        geo = _geocode_destination(destination)
        if geo.get("ok"):
            return {
                "ok": True,
                "destination": destination,
                "lat": geo["lat"],
                "lon": geo["lon"],
                "displayName": geo.get("displayName") or destination,
                "weather": weather or {},
                "source": geo.get("source"),
            }
        return geo
    except Exception as exc:
        return {
            "ok": False,
            "error": "destination_lookup_failed",
            "destination": destination,
            "details": str(exc)[:300],
        }


def _distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _sample_points(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, count: int) -> List[Dict[str, Any]]:
    count = max(3, min(int(count or 5), 12))
    points = []
    for i in range(count):
        t = i / (count - 1)
        lat = origin_lat + (dest_lat - origin_lat) * t
        lon = origin_lon + (dest_lon - origin_lon) * t
        points.append({
            "index": i + 1,
            "progress": round(t, 3),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
        })
    return points


def _score_point(weather: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    reasons = []

    watchman = weather.get("watchman") or {}
    threat_score = _num(watchman.get("threat_score") or watchman.get("threatScore"))
    if threat_score is not None:
        score += int(threat_score)

    alerts = weather.get("alerts") or []
    if isinstance(alerts, list) and alerts:
        score += min(45, len(alerts) * 20)
        reasons.append(f"{len(alerts)} active alert(s)")

    condition = _text(
        weather.get("condition")
        or weather.get("shortForecast")
        or _dig(weather, ["current", "condition"])
        or _dig(weather, ["forecast", "shortForecast"])
    )

    lower = condition.lower()
    risk_terms = [
        ("tornado", 100),
        ("severe thunderstorm", 85),
        ("thunderstorm", 45),
        ("lightning", 55),
        ("hail", 70),
        ("flood", 70),
        ("heavy rain", 55),
        ("fog", 35),
        ("wind", 35),
        ("snow", 45),
        ("ice", 65),
    ]

    for term, pts in risk_terms:
        if term in lower:
            score += pts
            reasons.append(term)

    precip = _num(weather.get("precipChance") or weather.get("precip_chance") or _dig(weather, ["current", "precipChance"]))
    if precip is not None and precip >= 60:
        score += 20
        reasons.append(f"{int(precip)}% precipitation chance")

    score = max(0, min(score, 100))

    if score >= 75:
        verdict = "dangerous"
    elif score >= 40:
        verdict = "caution"
    else:
        verdict = "clear"

    return {
        "score": score,
        "verdict": verdict,
        "reasons": reasons[:6],
        "condition": condition,
    }


def plan_route_weather(origin_lat: Any, origin_lon: Any, destination: str, samples: int = 5) -> Dict[str, Any]:
    o_lat = _num(origin_lat)
    o_lon = _num(origin_lon)

    if o_lat is None or o_lon is None:
        return {"ok": False, "error": "origin_gps_required"}

    dest = _destination_to_gps(destination)
    if not dest.get("ok"):
        return dest

    d_lat = float(dest["lat"])
    d_lon = float(dest["lon"])

    points = _sample_points(o_lat, o_lon, d_lat, d_lon, samples)
    total_miles = _distance_miles(o_lat, o_lon, d_lat, d_lon)

    scanned = []
    worst_score = 0
    worst_point = None

    for point in points:
        try:
            from app import _fetch_weather_direct
            weather = weather_lookup_for_gps("Route point", point["lat"], point["lon"], _fetch_weather_direct)
            risk = _score_point(weather if isinstance(weather, dict) else {})
        except Exception as exc:
            weather = {"error": str(exc)[:200]}
            risk = {"score": 0, "verdict": "unknown", "reasons": ["weather lookup failed"], "condition": ""}

        mile_marker = total_miles * point["progress"]

        item = {
            **point,
            "mile": round(mile_marker, 1),
            "risk": risk,
            "weather": weather,
        }

        scanned.append(item)

        if risk.get("score", 0) > worst_score:
            worst_score = risk.get("score", 0)
            worst_point = item

    if worst_score >= 75:
        verdict = "dangerous"
        recommendation = "I would not start this drive unless it is necessary. Weather risk is high somewhere on the route."
    elif worst_score >= 40:
        verdict = "caution"
        recommendation = "Use caution. Watchman found weather risk along the route."
    else:
        verdict = "clear"
        recommendation = "Route looks acceptable from the sampled weather points."

    summary = {
        "verdict": verdict,
        "score": worst_score,
        "recommendation": recommendation,
        "worstPoint": worst_point,
        "distanceMiles": round(total_miles, 1),
        "sampleCount": len(scanned),
    }

    return {
        "ok": True,
        "mode": "Watchman Route Planner",
        "origin": {"lat": o_lat, "lon": o_lon},
        "destination": {"name": destination, "lat": d_lat, "lon": d_lon},
        "summary": summary,
        "points": scanned,
    }
