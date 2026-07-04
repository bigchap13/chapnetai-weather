from __future__ import annotations

import re
from typing import Any, Dict, List


DOMAIN_KEYWORDS = {
    "real_life": {
        "label": "Real-Life Question Intelligence",
        "weight": 9,
        "terms": [
            "should i", "would you", "if you were me", "what should i do",
            "is it gonna", "gonna", "suck", "worth it", "better", "worse",
            "what am i missing", "tell me something", "what worries you",
        ],
    },
    "travel": {
        "label": "Travel Companion",
        "weight": 8,
        "terms": [
            "trip", "route", "drive", "leave", "wait", "arrive", "destination",
            "eta", "different route", "safer route", "beat the storm", "Biloxi",
        ],
    },
    "road": {
        "label": "Road Intelligence",
        "weight": 7,
        "terms": [
            "road", "interstate", "highway", "i-", "us-", "closed", "closure",
            "construction", "traffic", "wreck", "icy", "slick", "flooded road",
        ],
    },
    "vehicle": {
        "label": "Vehicle Intelligence",
        "weight": 7,
        "terms": [
            "tow", "towing", "trailer", "camper", "rv", "truck", "semi",
            "motorcycle", "ev", "range", "crosswind", "braking",
        ],
    },
    "local_services": {
        "label": "Local Services",
        "weight": 6,
        "terms": [
            "gas", "fuel", "charger", "ev charger", "food", "coffee",
            "hotel", "hospital", "er", "tow truck", "bathroom", "rest area",
        ],
    },
    "outdoor": {
        "label": "Outdoor Intelligence",
        "weight": 6,
        "terms": [
            "fish", "fishing", "boat", "hike", "camp", "hunt", "golf",
            "mow", "roof", "lake", "beach", "outside",
        ],
    },
    "emergency": {
        "label": "Emergency Intelligence",
        "weight": 10,
        "terms": [
            "emergency", "help", "tornado warning", "shelter", "flash flood",
            "floodwater", "evacuate", "stranded", "heat stroke", "911",
            "danger", "trapped",
        ],
    },
    "geo": {
        "label": "Geography Knowledge",
        "weight": 4,
        "terms": [
            "state", "city", "country", "canada", "mexico", "alabama",
            "texas", "florida", "california", "georgia", "mississippi",
        ],
    },
    "highway": {
        "label": "Highway Knowledge",
        "weight": 5,
        "terms": [
            "i-10", "i-20", "i-22", "i-40", "i-59", "i-65", "i-75",
            "i-85", "i-95", "us-78", "highway", "interstate",
        ],
    },
}


def clean_question(question: str) -> str:
    q = (question or "").strip()
    q = re.sub(r"^\s*(hey\s+)?(ok\s+|okay\s+)?watchman[,:\s]+", "", q, flags=re.I)
    q = re.sub(r"[,:\s]+watchman\s*$", "", q, flags=re.I)
    return q.strip()


def _term_score(question: str, terms: List[str]) -> int:
    q = question.lower()
    score = 0

    for term in terms:
        t = term.lower()
        if " " in t or "-" in t:
            if t in q:
                score += 3
        else:
            if re.search(r"\b" + re.escape(t) + r"\b", q):
                score += 1

    return score


def detect_domains(question: str) -> List[Dict[str, Any]]:
    cleaned = clean_question(question)
    ranked: List[Dict[str, Any]] = []

    for domain, data in DOMAIN_KEYWORDS.items():
        raw_score = _term_score(cleaned, data["terms"])
        if raw_score:
            ranked.append({
                "domain": domain,
                "label": data["label"],
                "score": raw_score * data["weight"],
                "rawScore": raw_score,
            })

    # Emergency always gets priority when present.
    q = cleaned.lower()
    if any(t in q for t in ["911", "tornado warning", "flash flood", "floodwater", "evacuate", "stranded", "heat stroke"]):
        for item in ranked:
            if item["domain"] == "emergency":
                item["score"] += 50

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def route_question(question: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    context = context or {}
    cleaned = clean_question(question)
    domains = detect_domains(cleaned)

    if not domains:
        domains = [{
            "domain": "real_life",
            "label": "Real-Life Question Intelligence",
            "score": 25,
            "rawScore": 1,
        }]

    lead = domains[0]
    supporting = domains[1:5]

    reason_bits = []
    if lead["domain"] == "emergency":
        reason_bits.append("Emergency/safety language takes priority.")
    if len(domains) > 1:
        reason_bits.append("Question touches multiple Watchman modules.")
    else:
        reason_bits.append("Question has one clear lead module.")

    return {
        "ok": True,
        "mode": "Watchman Brain Router V1",
        "question": question,
        "cleanedQuestion": cleaned,
        "leadSkill": lead,
        "supportingSkills": supporting,
        "allMatches": domains,
        "multiSkill": len(domains) > 1,
        "reason": " ".join(reason_bits),
    }


def _call_domain(domain: str, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    weather = context.get("weather") or {}
    route_payload = context.get("route") or {}

    try:
        if domain == "real_life":
            from .real_life_questions import answer_real_life_question
            return answer_real_life_question(question, context)

        if domain == "travel":
            from .travel_companion import answer_travel_question
            return answer_travel_question(question, route_payload, context.get("destination"))

        if domain == "road":
            from .road_intelligence import answer_road_question
            return answer_road_question(question, route_payload)

        if domain == "vehicle":
            from .vehicle_intelligence import answer_vehicle_question
            return answer_vehicle_question(question, weather, route_payload)

        if domain == "local_services":
            from .local_services import answer_local_service_question
            return answer_local_service_question(question, route_payload)

        if domain == "outdoor":
            from .outdoor_intelligence import answer_outdoor_question
            return answer_outdoor_question(question, weather)

        if domain == "emergency":
            from .emergency_intelligence_v1 import answer_emergency_question
            return answer_emergency_question(question, weather, route_payload)

        if domain == "geo":
            from .geo_knowledge import answer_geo_question
            return answer_geo_question(question)

        if domain == "highway":
            from .highway_knowledge import answer_highway_question
            return answer_highway_question(question)

    except Exception as exc:
        return {
            "ok": False,
            "mode": "Watchman Brain Router V1",
            "domain": domain,
            "error": str(exc)[:300],
        }

    return {
        "ok": True,
        "handled": False,
        "domain": domain,
        "answer": "No module handler available for this domain yet.",
    }


def answer_with_brain(question: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    context = context or {}
    routed = route_question(question, context)
    cleaned = routed["cleanedQuestion"]

    lead_domain = routed["leadSkill"]["domain"]
    lead_answer = _call_domain(lead_domain, cleaned, context)

    support_answers = []
    for item in routed["supportingSkills"]:
        support_answers.append({
            "domain": item["domain"],
            "label": item["label"],
            "result": _call_domain(item["domain"], cleaned, context),
        })

    answer_text = lead_answer.get("answer") or "Watchman routed the question, but the lead module did not return an answer."

    domains = [lead_domain] + [x["domain"] for x in routed["supportingSkills"]]
    ql = cleaned.lower()

    if "vehicle" in domains and "travel" in domains and ("tonight" in ql or "tomorrow" in ql or "wait" in ql):
        answer_text = (
            "This is a combined trip decision, not just a forecast question. "
            "I would judge the route, towing risk, road conditions, tonight-versus-tomorrow timing, and destination conditions together. "
            "If wind, storms, flooded roads, or poor visibility affect the route tonight, waiting until tomorrow is probably the smarter move. "
            "If those hazards are not on the route, the trip may be reasonable."
        )
    elif "road" in domains and "travel" in domains and ("closed" in ql or "different route" in ql):
        answer_text = (
            "This is both a road-status and route-choice question. "
            "I need the active route or live road feed to confirm a closure, then I would decide whether to stay on the normal route or reroute."
        )
    elif "outdoor" in domains and "real_life" in domains and ("mow" in ql or "roof" in ql or "outside" in ql):
        answer_text = (
            "This is an outdoor-work decision. "
            "I would check rain timing, lightning, heat, wind, and whether the job is worth starting before conditions interrupt it."
        )

    if routed["multiSkill"]:
        support_labels = ", ".join(x["label"] for x in routed["supportingSkills"])
        if support_labels:
            answer_text += f" I also checked: {support_labels}."

    return {
        "ok": True,
        "mode": "Watchman Brain Router V1",
        "routing": routed,
        "leadResult": lead_answer,
        "supportResults": support_answers,
        "answer": answer_text,
    }


def brain_router_summary() -> Dict[str, Any]:
    return {
        "ok": True,
        "mode": "Watchman Brain Router V1",
        "domainCount": len(DOMAIN_KEYWORDS),
        "domains": DOMAIN_KEYWORDS,
        "purpose": "Routes natural questions across multiple Watchman intelligence modules and combines lead/supporting skill answers.",
    }
