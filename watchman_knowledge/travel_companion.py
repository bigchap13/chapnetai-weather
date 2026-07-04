from __future__ import annotations

from typing import Any, Dict, List

from .skills_registry import classify_question


TRAVEL_SKILL_IDS = {
    "TR-001",
    "TR-002",
    "TR-003",
    "TR-004",
    "TR-005",
    "TR-006",
    "RW-001",
    "RW-002",
    "RW-003",
    "RW-007",
}


def _text(v: Any, fallback: str = "") -> str:
    if v is None:
        return fallback
    return str(v).strip() or fallback


def _trip_summary(route_payload: Dict[str, Any]) -> Dict[str, Any]:
    route = route_payload.get("route") or {}
    summary = route_payload.get("summary") or {}
    dest = route_payload.get("destination") or {}

    return {
        "destination": dest.get("name") or "",
        "distanceMiles": route.get("distanceMiles"),
        "durationMinutes": route.get("durationMinutes"),
        "verdict": summary.get("verdict"),
        "recommendation": summary.get("recommendation"),
        "routesCompared": summary.get("routesCompared"),
        "routeChoice": summary.get("routeChoice"),
        "worstPoint": summary.get("worstPoint"),
    }


def _format_minutes(minutes: Any) -> str:
    try:
        minutes = int(minutes or 0)
    except Exception:
        return "time unavailable"

    h = minutes // 60
    m = minutes % 60
    if h <= 0:
        return f"{m} min"
    if m == 0:
        return f"{h} hr"
    return f"{h} hr {m} min"


def answer_travel_question(
    question: str,
    route_payload: Dict[str, Any] | None = None,
    destination: str | None = None,
) -> Dict[str, Any]:
    question = _text(question)
    route_payload = route_payload or {}

    classified = classify_question(question)
    skill = classified.get("matchedSkill") or {}
    skill_id = skill.get("id") or "AI-008"

    if skill_id not in TRAVEL_SKILL_IDS and not skill_id.startswith("TR-") and not skill_id.startswith("RW-"):
        return {
            "ok": True,
            "mode": "Watchman Travel Companion",
            "handled": False,
            "skill": skill,
            "answer": "This does not look like a travel or route question. Watchman should hand this to another skill domain.",
        }

    trip = _trip_summary(route_payload) if route_payload else {}
    has_route = bool(route_payload.get("ok") and route_payload.get("route"))

    if not has_route:
        return {
            "ok": True,
            "mode": "Watchman Travel Companion",
            "handled": True,
            "skill": skill,
            "needsRoute": True,
            "answer": (
                "I can answer that, but I need an active route first. "
                "Give me a destination or plan a route, then I can judge ETA, arrival weather, route hazards, and departure timing."
            ),
        }

    route = route_payload.get("route") or {}
    summary = route_payload.get("summary") or {}
    points: List[Dict[str, Any]] = route_payload.get("weatherPoints") or []

    distance = trip.get("distanceMiles")
    duration = _format_minutes(trip.get("durationMinutes"))
    verdict = _text(summary.get("verdict"), "unknown")
    recommendation = _text(summary.get("recommendation"), "No recommendation available.")

    avoid_points = [p for p in points if p.get("routeAction") == "avoid"]
    caution_points = [p for p in points if p.get("routeAction") == "caution"]
    monitor_points = [p for p in points if p.get("routeAction") == "monitor"]

    if skill_id == "TR-002":
        answer = (
            f"The normal fastest route is {distance} miles and about {duration}. "
            f"Watchman says: {recommendation}"
        )
    elif skill_id == "TR-003":
        if avoid_points:
            p = avoid_points[0]
            answer = (
                f"I would treat this as a weather-sensitive route. "
                f"The first avoid-level issue is near mile {p.get('mile')} around {p.get('etaMessage')}. "
                f"{p.get('driverMessage')}"
            )
        else:
            answer = (
                f"I do not see a reroute-level weather hazard on this route. "
                f"Stay on the normal route. {recommendation}"
            )
    elif skill_id == "TR-004":
        choices = route_payload.get("routeChoices") or []
        if len(choices) <= 1:
            answer = "I only have one usable route option right now."
        else:
            selected = next((c for c in choices if c.get("selected")), choices[0])
            answer = (
                f"I compared {len(choices)} route option(s). "
                f"The selected route is {selected.get('distanceMiles')} miles and about {_format_minutes(selected.get('durationMinutes'))}. "
                f"It has {selected.get('avoidPoints', 0)} avoid-level point(s) and {selected.get('cautionPoints', 0)} caution point(s)."
            )
    elif skill_id == "TR-005":
        dest_name = (route_payload.get("destination") or {}).get("name") or destination or "your destination"
        last = points[-1] if points else {}
        answer = (
            f"At {dest_name}, Watchman's route sample shows: "
            f"{last.get('explanation') or 'No major route weather concern detected.'} "
            f"Expected arrival point: {last.get('etaMessage') or duration}."
        )
    elif skill_id == "TR-006":
        if avoid_points:
            p = avoid_points[0]
            answer = (
                f"I would consider delaying or rerouting before leaving. "
                f"Watchman found an avoid-level issue near mile {p.get('mile')} around {p.get('etaMessage')}. "
                f"{p.get('driverMessage')}"
            )
        elif caution_points:
            p = caution_points[0]
            answer = (
                f"You can leave, but use caution. "
                f"The first driving-weather concern is near mile {p.get('mile')} around {p.get('etaMessage')}. "
                f"{p.get('driverMessage')}"
            )
        else:
            answer = "Leaving now looks reasonable. Watchman does not see a reroute-level weather hazard on this route."
    elif skill_id.startswith("RW-"):
        if avoid_points:
            p = avoid_points[0]
            answer = (
                f"The main route weather issue is near mile {p.get('mile')} around {p.get('etaMessage')}: "
                f"{p.get('explanation')}. {p.get('driverMessage')}"
            )
        elif caution_points:
            p = caution_points[0]
            answer = (
                f"The main driving-weather concern is near mile {p.get('mile')} around {p.get('etaMessage')}: "
                f"{p.get('explanation')}. {p.get('driverMessage')}"
            )
        elif monitor_points:
            p = monitor_points[0]
            answer = (
                f"I see weather information to monitor, but nothing that should change the route. "
                f"First note: mile {p.get('mile')} around {p.get('etaMessage')}: {p.get('explanation')}."
            )
        else:
            answer = "I do not see meaningful weather trouble along this route right now."
    else:
        answer = (
            f"This route is {distance} miles and about {duration}. "
            f"Status: {verdict}. {recommendation}"
        )

    return {
        "ok": True,
        "mode": "Watchman Travel Companion",
        "handled": True,
        "skill": skill,
        "classificationConfidence": classified.get("confidence"),
        "trip": trip,
        "answer": answer,
    }
