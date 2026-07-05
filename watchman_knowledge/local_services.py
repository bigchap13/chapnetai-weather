from __future__ import annotations
import re

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


SERVICE_MAP = {
    "gas": {
        "label": "gas stations",
        "queries": ['node["amenity"="fuel"](around:{radius},{lat},{lon});', 'way["amenity"="fuel"](around:{radius},{lat},{lon});'],
    },
    "fuel": {
        "label": "fuel stops",
        "queries": ['node["amenity"="fuel"](around:{radius},{lat},{lon});', 'way["amenity"="fuel"](around:{radius},{lat},{lon});'],
    },
    "ev": {
        "label": "EV chargers",
        "queries": ['node["amenity"="charging_station"](around:{radius},{lat},{lon});', 'way["amenity"="charging_station"](around:{radius},{lat},{lon});'],
    },
    "charger": {
        "label": "EV chargers",
        "queries": ['node["amenity"="charging_station"](around:{radius},{lat},{lon});', 'way["amenity"="charging_station"](around:{radius},{lat},{lon});'],
    },
    "hospital": {
        "label": "hospitals",
        "queries": ['node["amenity"="hospital"](around:{radius},{lat},{lon});', 'way["amenity"="hospital"](around:{radius},{lat},{lon});'],
    },
    "er": {
        "label": "emergency care",
        "queries": ['node["amenity"="hospital"](around:{radius},{lat},{lon});', 'node["healthcare"="hospital"](around:{radius},{lat},{lon});'],
    },
    "pharmacy": {
        "label": "pharmacies",
        "queries": ['node["amenity"="pharmacy"](around:{radius},{lat},{lon});', 'way["amenity"="pharmacy"](around:{radius},{lat},{lon});'],
    },
    "food": {
        "label": "food stops",
        "queries": ['node["amenity"="restaurant"](around:{radius},{lat},{lon});', 'node["amenity"="fast_food"](around:{radius},{lat},{lon});'],
    },
    "restaurant": {
        "label": "restaurants",
        "queries": ['node["amenity"="restaurant"](around:{radius},{lat},{lon});', 'node["amenity"="fast_food"](around:{radius},{lat},{lon});'],
    },
    "coffee": {
        "label": "coffee stops",
        "queries": ['node["amenity"="cafe"](around:{radius},{lat},{lon});'],
    },
    "hotel": {
        "label": "hotels",
        "queries": ['node["tourism"="hotel"](around:{radius},{lat},{lon});', 'way["tourism"="hotel"](around:{radius},{lat},{lon});', 'node["tourism"="motel"](around:{radius},{lat},{lon});'],
    },
    "motel": {
        "label": "motels",
        "queries": ['node["tourism"="motel"](around:{radius},{lat},{lon});', 'way["tourism"="motel"](around:{radius},{lat},{lon});'],
    },
    "bathroom": {
        "label": "bathrooms",
        "queries": ['node["amenity"="toilets"](around:{radius},{lat},{lon});'],
    },
    "restroom": {
        "label": "restrooms",
        "queries": ['node["amenity"="toilets"](around:{radius},{lat},{lon});'],
    },
    "rest area": {
        "label": "rest areas",
        "queries": ['node["highway"="rest_area"](around:{radius},{lat},{lon});', 'way["highway"="rest_area"](around:{radius},{lat},{lon});'],
    },
    "mechanic": {
        "label": "mechanics",
        "queries": ['node["shop"="car_repair"](around:{radius},{lat},{lon});', 'way["shop"="car_repair"](around:{radius},{lat},{lon});'],
    },
    "tow": {
        "label": "towing or repair help",
        "queries": ['node["shop"="car_repair"](around:{radius},{lat},{lon});', 'node["amenity"="fuel"](around:{radius},{lat},{lon});'],
    },
    "safe place": {
        "label": "safe nearby public places",
        "queries": ['node["amenity"="fuel"](around:{radius},{lat},{lon});', 'node["amenity"="hospital"](around:{radius},{lat},{lon});', 'node["amenity"="police"](around:{radius},{lat},{lon});'],
    },
    "pull over": {
        "label": "safe pull-over options",
        "queries": ['node["highway"="rest_area"](around:{radius},{lat},{lon});', 'node["amenity"="fuel"](around:{radius},{lat},{lon});', 'node["amenity"="parking"](around:{radius},{lat},{lon});'],
    },
    "police": {
        "label": "police stations",
        "queries": ['node["amenity"="police"](around:{radius},{lat},{lon});', 'way["amenity"="police"](around:{radius},{lat},{lon});'],
    },
}


def _service_key(question: str) -> str:
    q = (question or "").lower()

    if any(x in q for x in ["nearest er", " er", "emergency room", "urgent care"]):
        return "er"

    # Check longer / safety phrases first so "pull over" does not match "er".
    phrase_priority = [
        "safe place",
        "pull over",
        "rest area",
        "tow truck",
        "urgent care",
        "ev charger",
        "gas",
        "fuel",
        "charger",
        "hotel",
        "motel",
        "hospital",
        "pharmacy",
        "coffee",
        "restaurant",
        "food",
        "bathroom",
        "restroom",
        "mechanic",
        "towing",
        "tow",
        "police",
    ]

    for key in phrase_priority:
        if key in SERVICE_MAP and key in q:
            return key

    # Short keys must be real words, not inside another word.
    for key in SERVICE_MAP:
        if re.search(r"\\b" + re.escape(key) + r"\\b", q):
            return key

    return "safe place" if "safe" in q else "food"


def _distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt
    r = 3958.8
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(2 * r * asin(sqrt(a)), 1)


def _overpass(lat: float, lon: float, queries: List[str], radius: int = 12000) -> List[Dict[str, Any]]:
    body = "[out:json][timeout:20];(" + "".join(q.format(lat=lat, lon=lon, radius=radius) for q in queries) + ");out center tags 25;"
    data = urllib.parse.urlencode({"data": body}).encode()
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"User-Agent": "ChapNetAI-Watchman/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        payload = json.loads(res.read().decode("utf-8"))
    return payload.get("elements", [])


def answer_local_service_question(question: str, route_payload: Dict[str, Any] | None = None, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    context = context or {}
    route_payload = route_payload or {}

    gps = context.get("gps") or {}
    location = context.get("location") or {}

    lat = gps.get("lat") or location.get("lat") or route_payload.get("lat") or context.get("lat")
    lon = gps.get("lon") or location.get("lon") or route_payload.get("lon") or context.get("lon")
    place = context.get("place") or location.get("name") or "your current location"

    if not lat or not lon:
        return {
            "ok": True,
            "handled": True,
            "mode": "Watchman Local Services",
            "decision": "needs_gps",
            "answer": "I can find that, but I need GPS permission so I know where to search from.",
        }

    lat = float(lat)
    lon = float(lon)

    key = _service_key(question)
    service = SERVICE_MAP.get(key) or SERVICE_MAP["food"]

    try:
        raw = _overpass(lat, lon, service["queries"])
    except Exception as exc:
        return {
            "ok": True,
            "handled": True,
            "mode": "Watchman Local Services",
            "decision": "provider_unavailable",
            "answer": f"I understood this as a request for {service['label']}, but the live place-search provider did not answer right now: {str(exc)[:100]}",
        }

    results = []
    seen = set()

    for item in raw:
        tags = item.get("tags") or {}
        name = tags.get("name") or tags.get("brand") or service["label"].title()
        item_lat = item.get("lat") or (item.get("center") or {}).get("lat")
        item_lon = item.get("lon") or (item.get("center") or {}).get("lon")
        if item_lat is None or item_lon is None:
            continue

        miles = _distance_miles(lat, lon, float(item_lat), float(item_lon))
        ident = (name.lower(), round(float(item_lat), 4), round(float(item_lon), 4))
        if ident in seen:
            continue
        seen.add(ident)

        results.append({
            "name": name,
            "distanceMiles": miles,
            "lat": float(item_lat),
            "lon": float(item_lon),
            "type": tags.get("amenity") or tags.get("tourism") or tags.get("shop") or tags.get("highway") or key,
            "address": ", ".join(x for x in [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:city"),
                tags.get("addr:state"),
            ] if x),
        })

    results.sort(key=lambda x: x["distanceMiles"])
    top = results[:5]

    if not top:
        return {
            "ok": True,
            "handled": True,
            "mode": "Watchman Local Services",
            "decision": "none_found",
            "answer": f"I searched near {place}, but I did not find nearby {service['label']} in the live map data.",
            "results": [],
        }

    parts = []
    for i, r in enumerate(top, 1):
        addr = f" — {r['address']}" if r.get("address") else ""
        parts.append(f"{i}. {r['name']} ({r['distanceMiles']} mi){addr}")

    return {
        "ok": True,
        "handled": True,
        "mode": "Watchman Local Services",
        "decision": "found",
        "answer": f"Nearest {service['label']} near {place}: " + " ".join(parts),
        "results": top,
        "provider": "OpenStreetMap Overpass",
    }


def local_services_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Local Services",
        "services": sorted(SERVICE_MAP.keys()),
        "provider": "OpenStreetMap Overpass",
    }
