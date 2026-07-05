from __future__ import annotations

import re
from typing import Any, Dict, List


OUTDOOR_ACTIVITIES: Dict[str, Dict[str, Any]] = {
    "fishing": {
        "label": "Fishing",
        "terms": ["fish", "fishing", "lake", "pond", "river bank"],
        "watch": ["lightning", "wind", "heavy rain", "flooding", "heat", "cold front"],
    },
    "boating": {
        "label": "Boating",
        "terms": ["boat", "boating", "kayak", "canoe", "lake", "river"],
        "watch": ["wind", "gusts", "lightning", "waves", "visibility", "cold water"],
    },
    "hiking": {
        "label": "Hiking",
        "terms": ["hike", "hiking", "trail", "walk in the woods"],
        "watch": ["lightning", "heat", "flooding", "fog", "wind", "nightfall"],
    },
    "camping": {
        "label": "Camping",
        "terms": ["camp", "camping", "campground", "tent"],
        "watch": ["storms", "wind", "flooding", "cold", "heat", "fire weather"],
    },
    "hunting": {
        "label": "Hunting",
        "terms": ["hunt", "hunting", "deer stand", "woods"],
        "watch": ["wind direction", "lightning", "fog", "cold", "heat", "visibility"],
    },
    "golf": {
        "label": "Golf",
        "terms": ["golf", "golfing", "tee time"],
        "watch": ["lightning", "rain", "wind", "heat", "cart path conditions"],
    },
    "beach": {
        "label": "Beach",
        "terms": ["beach", "surf", "swim", "swimming"],
        "watch": ["rip currents", "lightning", "heat", "wind", "surf", "tropical weather"],
    },
    "motorcycle": {
        "label": "Motorcycle Riding",
        "terms": ["motorcycle", "bike ride", "ride my bike", "riding"],
        "watch": ["rain", "wet roads", "wind", "lightning", "fog", "heat"],
    },
    "outdoor_work": {
        "label": "Outdoor Work",
        "terms": ["mow", "roof", "yard work", "outside work", "work outside"],
        "watch": ["heat", "lightning", "rain", "wind", "humidity"],
    },
}


def classify_outdoor_question(question: str) -> Dict[str, Any]:
    q = (question or "").lower()
    matches: List[Dict[str, Any]] = []

    for key, data in OUTDOOR_ACTIVITIES.items():
        score = 0
        for term in data.get("terms", []):
            if re.search(r"\b" + re.escape(term) + r"\b", q):
                score += 2 if " " in term else 1
        if score:
            matches.append({"activity": key, "score": score, **data})

    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"handled": bool(matches), "best": matches[0] if matches else None, "matches": matches}


def _weather_text(weather: Dict[str, Any]) -> str:
    parts: List[str] = []

    for a in weather.get("alerts") or []:
        if isinstance(a, dict):
            parts.append(str(a.get("event") or ""))
            parts.append(str(a.get("headline") or ""))

    obs = weather.get("observation") or {}
    for key in ["textDescription", "temperatureF", "windMph", "gustMph"]:
        if obs.get(key) is not None:
            parts.append(str(obs.get(key)))

    for p in (weather.get("forecast") or [])[:3]:
        if isinstance(p, dict):
            parts.append(str(p.get("shortForecast") or ""))
            parts.append(str(p.get("detailedForecast") or ""))

    return " ".join(parts).lower()


def outdoor_activity_decision(activity: str, weather: Dict[str, Any] | None = None) -> Dict[str, Any]:
    weather = weather or {}
    data = OUTDOOR_ACTIVITIES.get(activity) or {}
    label = data.get("label", activity)
    text = _weather_text(weather)

    avoid_terms = ["tornado", "severe thunderstorm warning", "flash flood", "lightning", "blizzard", "ice storm"]
    caution_terms = ["thunderstorm", "heavy rain", "high wind", "gust", "fog", "heat advisory", "flood", "smoke", "air quality"]

    if any(t in text for t in avoid_terms):
        decision = "avoid"
        recommendation = f"Do not do {label.lower()} right now. Watchman sees a dangerous outdoor hazard."
    elif any(t in text for t in caution_terms):
        decision = "caution"
        recommendation = f"Use caution for {label.lower()}. Conditions may be workable, but Watchman sees weather that could affect safety."
    else:
        decision = "good"
        recommendation = f"{label} looks reasonable from the current information Watchman has."

    return {
        "decision": decision,
        "recommendation": recommendation,
        "watchFactors": data.get("watch", []),
    }


def answer_outdoor_question(question: str, weather: Dict[str, Any] | None = None) -> Dict[str, Any]:
    classified = classify_outdoor_question(question)

    if not classified["handled"]:
        return {
            "ok": True,
            "mode": "Watchman Outdoor Intelligence",
            "handled": False,
            "answer": "I did not detect an outdoor activity. Ask about fishing, boating, hiking, camping, hunting, golf, beaches, motorcycle riding, mowing, roofing, or outdoor work.",
        }

    best = classified["best"]
    decision = outdoor_activity_decision(best["activity"], weather)

    return {
        "ok": True,
        "mode": "Watchman Outdoor Intelligence",
        "handled": True,
        "activity": best["activity"],
        "label": best["label"],
        "decision": decision["decision"],
        "watchFactors": decision["watchFactors"],
        "answer": decision["recommendation"] + " Watchman watches: " + ", ".join(decision["watchFactors"]) + ".",
    }


def outdoor_registry_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Outdoor Intelligence V1",
        "activityCount": len(OUTDOOR_ACTIVITIES),
        "activities": OUTDOOR_ACTIVITIES,
    }
