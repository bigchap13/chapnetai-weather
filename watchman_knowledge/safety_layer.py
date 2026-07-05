from __future__ import annotations

import json
import math
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _num(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _overpass(query: str) -> Dict[str, Any]:
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={
            "User-Agent": "ChapNetAI-Watchman-SafetyLayer/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode("utf-8"))


def safety_layer(lat: Any, lon: Any, radius_meters: Any = 10000) -> Dict[str, Any]:
    lat = _num(lat)
    lon = _num(lon)
    try:
        radius = int(float(radius_meters or 10000))
    except Exception:
        radius = 10000

    radius = max(1000, min(radius, 50000))

    if lat is None or lon is None:
        return {"ok": False, "error": "gps_required"}

    query = f"""
[out:json][timeout:20];
(
  node(around:{radius},{lat},{lon})[amenity=police];
  node(around:{radius},{lat},{lon})[amenity=hospital];
  node(around:{radius},{lat},{lon})[amenity=police];
  node(around:{radius},{lat},{lon})[amenity=hospital];
  way(around:{radius},{lat},{lon})[amenity=police];
  way(around:{radius},{lat},{lon})[amenity=hospital];
  way(around:{radius},{lat},{lon})[amenity=police];
  way(around:{radius},{lat},{lon})[amenity=hospital];
);
out center tags 80;
"""

    try:
        payload = _overpass(query)
    except Exception as exc:
        return {"ok": False, "error": "safety_lookup_failed", "details": str(exc)[:300]}

    places: List[Dict[str, Any]] = []

    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        center = el.get("center") or {}
        plat = _num(el.get("lat") or center.get("lat"))
        plon = _num(el.get("lon") or center.get("lon"))
        if plat is None or plon is None:
            continue

        amenity = tags.get("amenity") or tags.get("emergency") or "safety"
        name = tags.get("name") or tags.get("operator") or amenity.replace("_", " ").title()

        if amenity == "parking":
            kind = "safe_parking"
            label = "Safe parking"
        elif amenity == "police":
            kind = "police"
            label = "Police / sheriff"
        elif amenity == "hospital":
            kind = "hospital"
            label = "Hospital"
        elif amenity == "fire_station":
            kind = "fire_station"
            label = "Fire station"
        elif amenity == "shelter":
            kind = "shelter"
            label = "Shelter"
        elif amenity == "assembly_point":
            kind = "assembly_point"
            label = "Emergency assembly point"
        else:
            kind = str(amenity)
            label = str(amenity).replace("_", " ").title()

        places.append({
            "kind": kind,
            "label": label,
            "name": name,
            "lat": plat,
            "lon": plon,
            "distanceMiles": round(_distance_miles(lat, lon, plat, plon), 2),
        })

    places.sort(key=lambda x: x.get("distanceMiles", 9999))

    return {
        "ok": True,
        "mode": "Watchman Safety Layer",
        "center": {"lat": lat, "lon": lon},
        "radiusMeters": radius,
        "count": len(places),
        "places": places[:60],
        "note": "Public safety places from OpenStreetMap. Not police tracking or law-enforcement evasion.",
    }


def road_speed_limit(lat: Any, lon: Any) -> Dict[str, Any]:
    lat = _num(lat)
    lon = _num(lon)

    if lat is None or lon is None:
        return {"ok": False, "error": "gps_required"}

    query = f"""
[out:json][timeout:12];
way(around:35,{lat},{lon})[highway][maxspeed];
out tags center 10;
"""

    try:
        payload = _overpass(query)
    except Exception as exc:
        return {"ok": False, "error": "speed_limit_lookup_failed", "details": str(exc)[:200]}

    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        raw = str(tags.get("maxspeed") or "").strip()
        if not raw:
            continue

        mph = _parse_speed_mph(raw)
        return {
            "ok": True,
            "speedLimitRaw": raw,
            "speedLimitMph": mph,
            "road": tags.get("name") or "",
            "source": "openstreetmap_maxspeed",
        }

    return {
        "ok": True,
        "speedLimitRaw": "",
        "speedLimitMph": None,
        "source": "unavailable",
    }


def _parse_speed_mph(raw: str) -> Optional[int]:
    s = raw.lower().strip()
    m = re.search(r"(\\d+(?:\\.\\d+)?)", s)
    if not m:
        return None

    value = float(m.group(1))

    if "km" in s:
        return round(value * 0.621371)

    return round(value)
