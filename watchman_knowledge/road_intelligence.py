from __future__ import annotations

from typing import Any, Dict, List

from .highway_knowledge import extract_highways, describe_highway


ROAD_CLOSURE_TERMS = [
    "road closed", "closure", "closed", "blocked", "impassable",
    "do not travel", "travel prohibited", "shutdown",
]

ROAD_WEATHER_TERMS = [
    "ice", "icy", "slick", "black ice", "freezing rain", "snow", "flood", "flooded",
    "fog", "low visibility", "high wind", "crosswind", "debris",
]

ROAD_TRAFFIC_TERMS = [
    "wreck", "accident", "crash", "construction", "road work",
    "backup", "traffic", "delay", "detour",
]


def _lower(question: str) -> str:
    return (question or "").strip().lower()


def classify_road_question(question: str) -> Dict[str, Any]:
    q = _lower(question)

    if any(t in q for t in ROAD_CLOSURE_TERMS):
        intent = "closure"
    elif any(t in q for t in ROAD_WEATHER_TERMS):
        intent = "weather_road_condition"
    elif any(t in q for t in ROAD_TRAFFIC_TERMS):
        intent = "traffic_or_construction"
    elif "safe" in q or "dangerous" in q:
        intent = "road_safety"
    else:
        intent = "general_road_intelligence"

    return {
        "intent": intent,
        "highways": extract_highways(question),
    }


def answer_road_question(question: str, route_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    route_payload = route_payload or {}
    classified = classify_road_question(question)
    highways = [describe_highway(h) for h in classified.get("highways", [])]

    route_points: List[Dict[str, Any]] = route_payload.get("weatherPoints") or []
    avoid_points = [p for p in route_points if p.get("routeAction") == "avoid"]
    caution_points = [p for p in route_points if p.get("routeAction") == "caution"]

    intent = classified["intent"]

    if intent == "closure":
        if avoid_points:
            p = avoid_points[0]
            answer = (
                f"Watchman found an avoid-level road concern near mile {p.get('mile')} "
                f"around {p.get('etaMessage')}: {p.get('explanation')}. {p.get('driverMessage')}"
            )
        else:
            answer = (
                "I do not have a confirmed closure in the active route data. "
                "If this is a live DOT closure question, Watchman needs a DOT/traffic feed connected next."
            )
    elif intent == "weather_road_condition":
        if avoid_points:
            p = avoid_points[0]
            answer = (
                f"Road-weather risk is high near mile {p.get('mile')} around {p.get('etaMessage')}: "
                f"{p.get('explanation')}. {p.get('driverMessage')}"
            )
        elif caution_points:
            p = caution_points[0]
            answer = (
                f"There is a driving-weather concern near mile {p.get('mile')} around {p.get('etaMessage')}: "
                f"{p.get('explanation')}. {p.get('driverMessage')}"
            )
        else:
            answer = "I do not see road-weather conditions that should change the route right now."
    elif intent == "traffic_or_construction":
        answer = (
            "Traffic and construction intelligence is recognized, but live DOT/incident feeds are not connected yet. "
            "This module is ready to receive closures, construction, wrecks, detours, and delay feeds."
        )
    elif intent == "road_safety":
        if avoid_points:
            answer = "I would avoid or delay this route because Watchman found an avoid-level road hazard."
        elif caution_points:
            answer = "I would drive it with caution. Watchman found road concerns but not an automatic reroute condition."
        else:
            answer = "The route looks drivable from the current Watchman road intelligence available."
    else:
        answer = (
            "Road Intelligence is active. I can reason about closures, ice, flooding, fog, high wind, construction, "
            "wrecks, detours, highway corridors, and whether a road condition should change the route."
        )

    if highways:
        h = highways[0]
        answer += f" Highway context: {h.get('name')} — {h.get('corridor')}."

    return {
        "ok": True,
        "mode": "Watchman Road Intelligence",
        "intent": intent,
        "highways": highways,
        "answer": answer,
        "needsLiveDotFeed": intent in {"closure", "traffic_or_construction"},
    }


def road_registry_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Road Intelligence V1",
        "capabilities": [
            "closure intent recognition",
            "road-weather hazard reasoning",
            "highway extraction",
            "active route hazard interpretation",
            "traffic/construction placeholder for DOT feed integration",
        ],
    }
