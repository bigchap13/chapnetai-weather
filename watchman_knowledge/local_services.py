from __future__ import annotations

import re
from typing import Any, Dict, List


SERVICE_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "fuel": {
        "label": "Fuel",
        "terms": ["gas", "fuel", "diesel", "truck stop", "gas station"],
        "answer": "Watchman can help find fuel stops, diesel, truck stops, and better fuel opportunities ahead.",
    },
    "ev_charging": {
        "label": "EV Charging",
        "terms": ["ev", "charger", "charging", "tesla", "supercharger"],
        "answer": "Watchman can help find EV charging and plan charging stops along a route.",
    },
    "food": {
        "label": "Food and Coffee",
        "terms": ["food", "restaurant", "coffee", "breakfast", "lunch", "dinner", "bbq", "fast food"],
        "answer": "Watchman can help find food, coffee, fast stops, local favorites, and family-friendly restaurants.",
    },
    "lodging": {
        "label": "Hotels and Lodging",
        "terms": ["hotel", "motel", "room", "lodging", "campground", "rv park"],
        "answer": "Watchman can help find hotels, motels, campgrounds, RV parks, and pet-friendly lodging.",
    },
    "medical": {
        "label": "Medical",
        "terms": ["hospital", "er", "urgent care", "doctor", "clinic", "pharmacy", "medicine"],
        "answer": "Watchman can help find hospitals, ERs, urgent care, clinics, and pharmacies.",
    },
    "emergency_services": {
        "label": "Police and Fire",
        "terms": ["police", "sheriff", "fire station", "fire department", "911"],
        "answer": "Watchman can help locate police, sheriff offices, fire stations, and emergency services.",
    },
    "towing_repair": {
        "label": "Towing and Repair",
        "terms": ["tow", "towing", "mechanic", "repair", "tire shop", "flat tire", "battery"],
        "answer": "Watchman can help find towing, mechanics, tire shops, and roadside repair.",
    },
    "rest_area": {
        "label": "Rest Areas",
        "terms": ["rest area", "rest stop", "bathroom", "restroom", "pull over", "safe place to stop"],
        "answer": "Watchman can help find rest areas, bathrooms, safe pull-offs, and places to stop.",
    },
}


def classify_local_service(question: str) -> Dict[str, Any]:
    q = (question or "").lower()
    matches: List[Dict[str, Any]] = []

    for key, data in SERVICE_CATEGORIES.items():
        score = 0
        for term in data.get("terms", []):
            if re.search(r"\\b" + re.escape(term) + r"\\b", q):
                score += 2 if " " in term else 1
        if score:
            matches.append({"category": key, "score": score, **data})

    matches.sort(key=lambda x: x["score"], reverse=True)

    if matches:
        return {"handled": True, "best": matches[0], "matches": matches}

    return {"handled": False, "best": None, "matches": []}


def answer_local_service_question(question: str, route_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    route_payload = route_payload or {}
    classified = classify_local_service(question)

    if not classified["handled"]:
        return {
            "ok": True,
            "mode": "Watchman Local Services",
            "handled": False,
            "answer": "I did not detect a local-service request. Ask for gas, food, hotels, hospitals, towing, rest areas, pharmacies, or EV charging.",
        }

    best = classified["best"]
    route = route_payload.get("route") or {}
    has_route = bool(route_payload.get("ok") and route)

    route_context = ""
    if has_route:
        route_context = f" Active route: {route.get('distanceMiles')} miles, about {route.get('durationMinutes')} minutes."

    return {
        "ok": True,
        "mode": "Watchman Local Services",
        "handled": True,
        "category": best["category"],
        "label": best["label"],
        "answer": best["answer"] + route_context + " Live place-search/provider integration comes next.",
        "needsProvider": True,
        "providerTargets": [
            "OpenStreetMap / Overpass",
            "Google Places or compatible provider",
            "DOT rest area datasets",
            "EV charging provider",
            "fuel price provider",
        ],
    }


def local_services_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Local Services V1",
        "categoryCount": len(SERVICE_CATEGORIES),
        "categories": SERVICE_CATEGORIES,
        "phase": "V1 recognizes local-service intent. Next phase connects live place-search providers.",
    }
