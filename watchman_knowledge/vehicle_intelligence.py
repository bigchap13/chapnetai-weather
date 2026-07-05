from __future__ import annotations

import re
from typing import Any, Dict, List


VEHICLE_MODES: Dict[str, Dict[str, Any]] = {
    "car": {
        "label": "Car",
        "terms": ["car", "sedan", "suv", "van"],
        "watch": ["wet roads", "fog", "ice", "flooding", "visibility", "braking distance"],
    },
    "truck": {
        "label": "Truck",
        "terms": ["truck", "pickup"],
        "watch": ["crosswinds", "hydroplaning", "ice", "load stability", "flooding"],
    },
    "trailer": {
        "label": "Trailer / Towing",
        "terms": ["trailer", "tow", "towing", "camper", "boat trailer"],
        "watch": ["crosswinds", "gusts", "braking distance", "wet roads", "mountain grades"],
    },
    "rv": {
        "label": "RV",
        "terms": ["rv", "motorhome", "camper"],
        "watch": ["crosswinds", "height clearance", "mountain grades", "fuel stops", "safe pull-offs"],
    },
    "semi": {
        "label": "Semi Truck",
        "terms": ["semi", "tractor trailer", "18 wheeler", "big rig"],
        "watch": ["crosswinds", "chain laws", "mountain grades", "weigh stations", "braking distance"],
    },
    "motorcycle": {
        "label": "Motorcycle",
        "terms": ["motorcycle", "bike", "ride"],
        "watch": ["wet roads", "wind gusts", "lightning", "fog", "road spray", "heat"],
    },
    "ev": {
        "label": "Electric Vehicle",
        "terms": ["ev", "electric car", "tesla", "charging"],
        "watch": ["range loss", "charger spacing", "cold weather", "heat", "detours"],
    },
}


VEHICLE_CONCERN_TERMS = {
    "crosswind": ["crosswind", "wind", "gust", "bridge"],
    "traction": ["slick", "wet road", "ice", "snow", "hydroplane", "hydroplaning"],
    "heat": ["overheat", "engine heat", "hot", "heat"],
    "battery": ["battery", "charge", "charging", "range"],
    "braking": ["brake", "braking", "stopping distance"],
    "clearance": ["clearance", "low bridge", "height"],
}


def classify_vehicle_question(question: str) -> Dict[str, Any]:
    q = (question or "").lower()
    vehicle_matches: List[Dict[str, Any]] = []

    for key, data in VEHICLE_MODES.items():
        score = 0
        for term in data.get("terms", []):
            if re.search(r"\b" + re.escape(term) + r"\b", q):
                score += 2 if " " in term else 1
        if score:
            vehicle_matches.append({"vehicle": key, "score": score, **data})

    vehicle_matches.sort(key=lambda x: x["score"], reverse=True)

    concerns = []
    for concern, terms in VEHICLE_CONCERN_TERMS.items():
        if any(t in q for t in terms):
            concerns.append(concern)

    return {
        "handled": bool(vehicle_matches or concerns),
        "vehicle": vehicle_matches[0] if vehicle_matches else None,
        "vehicleMatches": vehicle_matches,
        "concerns": concerns,
    }


def _weather_text(weather: Dict[str, Any]) -> str:
    parts: List[str] = []
    for a in weather.get("alerts") or []:
        if isinstance(a, dict):
            parts.append(str(a.get("event") or ""))
            parts.append(str(a.get("headline") or ""))
    obs = weather.get("observation") or {}
    for key in ["textDescription", "windMph", "gustMph", "temperatureF"]:
        if obs.get(key) is not None:
            parts.append(str(obs.get(key)))
    for p in (weather.get("forecast") or [])[:3]:
        if isinstance(p, dict):
            parts.append(str(p.get("shortForecast") or ""))
            parts.append(str(p.get("detailedForecast") or ""))
    return " ".join(parts).lower()


def vehicle_decision(classified: Dict[str, Any], weather: Dict[str, Any] | None = None) -> Dict[str, Any]:
    weather = weather or {}
    text = _weather_text(weather)
    vehicle = classified.get("vehicle") or {}
    label = vehicle.get("label") or "Vehicle"

    avoid_terms = ["tornado", "flash flood", "ice storm", "blizzard", "road closed", "do not travel"]
    caution_terms = ["high wind", "gust", "fog", "heavy rain", "thunderstorm", "snow", "ice", "flood", "slick"]

    if any(t in text for t in avoid_terms):
        decision = "avoid"
        recommendation = f"Do not drive the {label.lower()} through this if you can avoid it."
    elif any(t in text for t in caution_terms):
        decision = "caution"
        recommendation = f"Use caution with the {label.lower()}. Watchman sees conditions that can affect handling or stopping distance."
    else:
        decision = "normal"
        recommendation = f"{label} travel looks normal from the current vehicle intelligence available."

    watch = vehicle.get("watch") or []
    concerns = classified.get("concerns") or []

    return {
        "decision": decision,
        "recommendation": recommendation,
        "watchFactors": watch,
        "concerns": concerns,
    }


def answer_vehicle_question(question: str, weather: Dict[str, Any] | None = None, route_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    route_payload = route_payload or {}
    classified = classify_vehicle_question(question)

    if not classified["handled"]:
        return {
            "ok": True,
            "mode": "Watchman Vehicle Intelligence",
            "handled": False,
            "answer": "I did not detect a vehicle-specific question. Ask about towing, trailers, RVs, motorcycles, EV range, braking, slick roads, crosswinds, or engine heat.",
        }

    decision = vehicle_decision(classified, weather)
    vehicle = classified.get("vehicle") or {}
    label = vehicle.get("label") or "Vehicle"

    route = route_payload.get("route") or {}
    route_context = ""
    if route_payload.get("ok") and route:
        route_context = f" Active route: {route.get('distanceMiles')} miles, about {route.get('durationMinutes')} minutes."

    return {
        "ok": True,
        "mode": "Watchman Vehicle Intelligence",
        "handled": True,
        "vehicle": vehicle.get("vehicle"),
        "label": label,
        "decision": decision["decision"],
        "concerns": decision["concerns"],
        "watchFactors": decision["watchFactors"],
        "answer": decision["recommendation"] + route_context + " Watchman watches: " + ", ".join(decision["watchFactors"] or decision["concerns"]) + ".",
    }


def vehicle_registry_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Vehicle Intelligence V1",
        "vehicleModeCount": len(VEHICLE_MODES),
        "vehicleModes": VEHICLE_MODES,
        "concernTypes": VEHICLE_CONCERN_TERMS,
    }
