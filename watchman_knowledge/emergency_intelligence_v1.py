from __future__ import annotations

import re
from typing import Any, Dict, List


EMERGENCY_TYPES: Dict[str, Dict[str, Any]] = {
    "tornado_shelter": {
        "label": "Tornado Shelter",
        "terms": ["tornado shelter", "storm shelter", "safe room", "basement", "where should i hide"],
        "severity": "life_safety",
        "answer": "Get to the lowest level, smallest interior room, away from windows. Cover your head and stay there until the warning expires or officials say it is safe.",
    },
    "flash_flood": {
        "label": "Flash Flood",
        "terms": ["flash flood", "flooded road", "flooded", "water over road", "turn around", "flood water", "floodwater", "should i cross", "cross water"],
        "severity": "life_safety",
        "answer": "Do not drive through floodwater. Turn around and find higher ground. A road can be washed out underneath even if the water looks shallow.",
    },
    "evacuation": {
        "label": "Evacuation",
        "terms": ["evacuate", "evacuation", "leave now", "escape route", "get out"],
        "severity": "life_safety",
        "answer": "Follow official evacuation orders first. Watchman can help reason about route weather and road risk, but official emergency instructions override route convenience.",
    },
    "medical": {
        "label": "Medical Emergency",
        "terms": ["hospital", "er", "urgent care", "ambulance", "medical emergency", "heart attack", "stroke"],
        "severity": "urgent_service",
        "answer": "For a medical emergency, call emergency services immediately. Watchman can help locate hospitals or urgent care once a live place provider is connected.",
    },
    "police_fire": {
        "label": "Police / Fire",
        "terms": ["police", "sheriff", "fire department", "fire station", "911", "crime", "wreck"],
        "severity": "urgent_service",
        "answer": "For immediate danger, call emergency services. Watchman can help locate police, fire, and sheriff offices once local-service providers are connected.",
    },
    "winter_survival": {
        "label": "Winter Travel Emergency",
        "terms": ["stranded", "stuck in snow", "ice storm", "blizzard", "freezing", "hypothermia"],
        "severity": "life_safety",
        "answer": "If stranded in winter conditions, stay with the vehicle if safe, conserve heat, keep exhaust clear if running the engine, and call emergency services.",
    },
    "heat_emergency": {
        "label": "Heat Emergency",
        "terms": ["heat stroke", "overheated", "too hot", "heat exhaustion", "dehydrated"],
        "severity": "life_safety",
        "answer": "Move to shade or air conditioning, cool the body, drink water if conscious, and seek emergency help for confusion, fainting, or signs of heat stroke.",
    },
    "safe_place": {
        "label": "Safe Place",
        "terms": ["safe place", "where should i go", "safe location", "pull over safely", "shelter nearby"],
        "severity": "safety_guidance",
        "answer": "Watchman should look for the nearest safe public place, shelter, hospital, police/fire station, hotel lobby, or well-lit stop depending on the threat.",
    },
}


def classify_emergency_question(question: str) -> Dict[str, Any]:
    q = (question or "").lower()
    matches: List[Dict[str, Any]] = []

    for key, data in EMERGENCY_TYPES.items():
        score = 0
        for term in data.get("terms", []):
            if re.search(r"\b" + re.escape(term) + r"\b", q):
                score += 2 if " " in term else 1
        if score:
            matches.append({"emergencyType": key, "score": score, **data})

    matches.sort(key=lambda x: x["score"], reverse=True)

    panic_terms = ["help", "emergency", "danger", "life threatening", "scared", "trapped"]
    panic_score = sum(1 for t in panic_terms if t in q)

    return {
        "handled": bool(matches or panic_score),
        "best": matches[0] if matches else None,
        "matches": matches,
        "panicScore": panic_score,
    }


def _weather_text(weather: Dict[str, Any]) -> str:
    parts: List[str] = []
    for a in weather.get("alerts") or []:
        if isinstance(a, dict):
            parts.append(str(a.get("event") or ""))
            parts.append(str(a.get("headline") or ""))
            parts.append(str(a.get("description") or ""))
            parts.append(str(a.get("instruction") or ""))
    for p in (weather.get("forecast") or [])[:2]:
        if isinstance(p, dict):
            parts.append(str(p.get("shortForecast") or ""))
            parts.append(str(p.get("detailedForecast") or ""))
    return " ".join(parts).lower()


def emergency_decision(classified: Dict[str, Any], weather: Dict[str, Any] | None = None) -> Dict[str, Any]:
    weather = weather or {}
    text = _weather_text(weather)

    best = classified.get("best") or {}
    etype = best.get("emergencyType") or "general_emergency"
    label = best.get("label") or "Emergency"
    severity = best.get("severity") or "unknown"

    life_terms = ["tornado warning", "flash flood warning", "evacuation", "blizzard warning", "ice storm warning"]
    if any(t in text for t in life_terms):
        severity = "life_safety"

    if severity == "life_safety":
        decision = "act_now"
    elif severity == "urgent_service":
        decision = "get_help"
    elif severity == "safety_guidance":
        decision = "find_safe_place"
    else:
        decision = "assess"

    return {
        "decision": decision,
        "emergencyType": etype,
        "label": label,
        "severity": severity,
    }


def answer_emergency_question(
    question: str,
    weather: Dict[str, Any] | None = None,
    route_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    route_payload = route_payload or {}
    classified = classify_emergency_question(question)

    if not classified["handled"]:
        return {
            "ok": True,
            "mode": "Watchman Emergency Intelligence",
            "handled": False,
            "answer": "I did not detect an emergency request. Ask about shelter, evacuation, flooded roads, tornado safety, hospitals, police, fire, or safe places.",
        }

    decision = emergency_decision(classified, weather)
    best = classified.get("best") or {}

    if best:
        answer = best.get("answer") or "Take immediate safety precautions."
    else:
        answer = "If this is an immediate emergency, call emergency services. Watchman can help reason about safe places, route hazards, and urgent services."

    route = route_payload.get("route") or {}
    if route_payload.get("ok") and route:
        answer += f" Active route context: {route.get('distanceMiles')} miles, about {route.get('durationMinutes')} minutes."

    return {
        "ok": True,
        "mode": "Watchman Emergency Intelligence",
        "handled": True,
        "decision": decision["decision"],
        "emergencyType": decision["emergencyType"],
        "label": decision["label"],
        "severity": decision["severity"],
        "panicScore": classified.get("panicScore", 0),
        "answer": answer,
        "important": "For immediate danger or medical emergencies, call local emergency services first.",
    }


def emergency_registry_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Emergency Intelligence V1",
        "emergencyTypeCount": len(EMERGENCY_TYPES),
        "emergencyTypes": EMERGENCY_TYPES,
        "phase": "V1 recognizes emergency intent and gives safety-oriented guidance. Later phases connect shelters, emergency management, hospitals, police/fire, and evacuation feeds.",
    }
