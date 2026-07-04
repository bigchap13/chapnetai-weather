from __future__ import annotations

from typing import Any, Dict, List


WATCHMAN_SKILL_DOMAINS: List[Dict[str, Any]] = [
    {
        "domainId": "WX",
        "name": "Weather Intelligence",
        "description": "Current weather, forecast, timing, changes, confidence, and explanations.",
        "skills": [
            {"id": "WX-001", "name": "Current Weather", "examples": ["What's it like outside?", "Weather now", "How hot is it?"]},
            {"id": "WX-002", "name": "Feels Like", "examples": ["What does it feel like?", "Heat index?", "Wind chill?"]},
            {"id": "WX-003", "name": "Hourly Forecast", "examples": ["Rain in the next 3 hours?", "Hourly forecast", "What happens this evening?"]},
            {"id": "WX-004", "name": "Daily Forecast", "examples": ["Tomorrow's weather?", "Forecast for today", "Weather this week?"]},
            {"id": "WX-005", "name": "Weather Timeline", "examples": ["What happens next?", "Show the weather timeline", "When does it change?"]},
            {"id": "WX-006", "name": "Weather Confidence", "examples": ["How confident are you?", "How sure is the forecast?", "What's the uncertainty?"]},
            {"id": "WX-007", "name": "Weather Explanation", "examples": ["Explain the forecast", "Why are you worried?", "Why is rain likely?"]},
        ],
    },
    {
        "domainId": "TR",
        "name": "Travel Intelligence",
        "description": "Trip planning, navigation, route choice, ETA, alternate routes, and arrival intelligence.",
        "skills": [
            {"id": "TR-001", "name": "Route Planning", "examples": ["Take me to Biloxi", "Plan a route", "Navigate to Nashville"]},
            {"id": "TR-002", "name": "Fastest Route", "examples": ["Fastest route", "Don't send me the long way", "Best normal route"]},
            {"id": "TR-003", "name": "Weather-Aware Route", "examples": ["Safest weather route", "Avoid dangerous weather", "Route around ice"]},
            {"id": "TR-004", "name": "Alternate Routes", "examples": ["Any better route?", "Compare routes", "Is there another way?"]},
            {"id": "TR-005", "name": "Arrival Forecast", "examples": ["What will weather be when I get there?", "Arrival weather", "Will it rain when I arrive?"]},
            {"id": "TR-006", "name": "Departure Timing", "examples": ["Should I leave now?", "Should I wait?", "Best time to leave?"]},
        ],
    },
    {
        "domainId": "RW",
        "name": "Route Weather",
        "description": "Weather hazards along the route using road geometry, GPS points, and ETA-aware hazard logic.",
        "skills": [
            {"id": "RW-001", "name": "Weather Along Route", "examples": ["Will I drive into storms?", "Weather on my route", "What's ahead?"]},
            {"id": "RW-002", "name": "Storm ETA", "examples": ["Will the storm still be there?", "Will it be gone before I get there?", "When do I hit rain?"]},
            {"id": "RW-003", "name": "Route Hazard ETA", "examples": ["When will I reach the hazard?", "How far until danger?", "ETA to storm?"]},
            {"id": "RW-004", "name": "Road Closure Weather", "examples": ["Any roads closed from ice?", "Flooded road ahead?", "Road closed due to weather?"]},
            {"id": "RW-005", "name": "Ice/Frozen Road Risk", "examples": ["Will roads freeze?", "Any ice on route?", "Freezing rain ahead?"]},
            {"id": "RW-006", "name": "Flood Route Risk", "examples": ["Will roads flood?", "Flash flood on route?", "Flooded crossings?"]},
            {"id": "RW-007", "name": "Route Timeline", "examples": ["Give me the trip timeline", "Weather by mile", "Weather by hour on this trip"]},
        ],
    },
    {
        "domainId": "RD",
        "name": "Road Intelligence",
        "description": "Closures, construction, traffic incidents, visibility, wind, road surface, and pass conditions.",
        "skills": [
            {"id": "RD-001", "name": "Road Closures", "examples": ["Any roads closed?", "Is the road blocked?", "Closures ahead?"]},
            {"id": "RD-002", "name": "Construction", "examples": ["Construction ahead?", "Road work?", "Any delays?"]},
            {"id": "RD-003", "name": "Icy Roads", "examples": ["Icy roads?", "Black ice?", "Are roads slick?"]},
            {"id": "RD-004", "name": "Flooded Roads", "examples": ["Flooded roads?", "Can I cross?", "Water over road?"]},
            {"id": "RD-005", "name": "Visibility", "examples": ["Fog ahead?", "Low visibility?", "Can I see to drive?"]},
            {"id": "RD-006", "name": "Crosswind Risk", "examples": ["Crosswinds?", "Safe for trailer?", "Wind on bridges?"]},
        ],
    },
    {
        "domainId": "SV",
        "name": "Severe Weather",
        "description": "Warnings, watches, storms, tornadoes, floods, winter weather, heat, smoke, and air quality.",
        "skills": [
            {"id": "SV-001", "name": "Tornado", "examples": ["Any tornado warning?", "Tornado near me?", "Is the tornado on my route?"]},
            {"id": "SV-002", "name": "Thunderstorm", "examples": ["Severe storm?", "Thunderstorm timing?", "Lightning nearby?"]},
            {"id": "SV-003", "name": "Flash Flood", "examples": ["Flash flood warning?", "Flooding risk?", "Should I avoid low roads?"]},
            {"id": "SV-004", "name": "Winter Storm", "examples": ["Snow on route?", "Blizzard?", "Ice storm?"]},
            {"id": "SV-005", "name": "High Wind", "examples": ["High wind warning?", "Wind dangerous?", "Trailer wind risk?"]},
            {"id": "SV-006", "name": "Heat/Air Quality", "examples": ["Heat advisory?", "Air quality?", "Smoke?"]},
        ],
    },
    {
        "domainId": "LS",
        "name": "Local Services",
        "description": "Food, fuel, hotels, rest areas, hospitals, police, towing, pharmacies, EV charging, and stops.",
        "skills": [
            {"id": "LS-001", "name": "Fuel", "examples": ["Find gas", "Cheapest fuel ahead", "Next gas stop"]},
            {"id": "LS-002", "name": "EV Charging", "examples": ["Find charger", "EV charger ahead", "Nearest charging station"]},
            {"id": "LS-003", "name": "Food/Coffee", "examples": ["Find food", "Coffee nearby", "BBQ ahead"]},
            {"id": "LS-004", "name": "Hotels", "examples": ["Hotel ahead", "Find a room", "Pet-friendly hotel"]},
            {"id": "LS-005", "name": "Hospitals", "examples": ["Nearest ER", "Hospital nearby", "Urgent care"]},
            {"id": "LS-006", "name": "Police/Fire", "examples": ["Police station nearby", "Fire station", "Sheriff office"]},
            {"id": "LS-007", "name": "Towing/Repair", "examples": ["Tow truck", "Mechanic nearby", "Tire shop"]},
            {"id": "LS-008", "name": "Rest Areas", "examples": ["Rest area ahead", "Bathroom stop", "Safe place to pull over"]},
        ],
    },
    {
        "domainId": "OD",
        "name": "Outdoor Intelligence",
        "description": "Fishing, hunting, hiking, boating, camping, beaches, lakes, rivers, golf, and outdoor work.",
        "skills": [
            {"id": "OD-001", "name": "Fishing", "examples": ["Good day to fish?", "Fishing weather", "Lake wind?"]},
            {"id": "OD-002", "name": "Boating", "examples": ["Safe to boat?", "Lake conditions", "Wind on the water?"]},
            {"id": "OD-003", "name": "Hiking/Camping", "examples": ["Safe to hike?", "Camping weather", "Storms in the park?"]},
            {"id": "OD-004", "name": "Motorcycle", "examples": ["Good day to ride?", "Motorcycle weather", "Rain on ride?"]},
            {"id": "OD-005", "name": "Outdoor Work", "examples": ["Can I mow?", "Can I roof today?", "Heat risk working outside?"]},
        ],
    },
    {
        "domainId": "VH",
        "name": "Vehicle Intelligence",
        "description": "Vehicle, trailer, RV, tire, engine heat, battery, braking, and load-risk advice.",
        "skills": [
            {"id": "VH-001", "name": "Trailer Safety", "examples": ["Safe to tow?", "Trailer wind risk", "Crosswind with trailer?"]},
            {"id": "VH-002", "name": "RV/Semi", "examples": ["Safe for RV?", "Semi wind risk", "High profile vehicle?"]},
            {"id": "VH-003", "name": "Engine Heat", "examples": ["Will heat affect my truck?", "Overheating risk?", "Mountain heat?"]},
            {"id": "VH-004", "name": "Tires/Braking", "examples": ["Slick roads?", "Braking distance?", "Tire weather risk?"]},
            {"id": "VH-005", "name": "Speed Awareness", "examples": ["What's the speed limit?", "How fast am I going?", "Am I speeding?"]},
        ],
    },
    {
        "domainId": "EM",
        "name": "Emergency Intelligence",
        "description": "Shelter, evacuation, emergency routing, disaster guidance, safe places, and urgent services.",
        "skills": [
            {"id": "EM-001", "name": "Shelter Finder", "examples": ["Find shelter", "Where do I go?", "Safe place nearby"]},
            {"id": "EM-002", "name": "Evacuation Route", "examples": ["Evacuation route", "How do I get out?", "Safest escape route"]},
            {"id": "EM-003", "name": "Emergency Services", "examples": ["Nearest hospital", "Call help", "Police nearby"]},
            {"id": "EM-004", "name": "Disaster Updates", "examples": ["Power outage?", "Flood update", "Emergency update"]},
        ],
    },
    {
        "domainId": "AI",
        "name": "Watchman AI Companion",
        "description": "Conversational reasoning, explanation, proactive monitoring, memory, and personal companion behavior.",
        "skills": [
            {"id": "AI-001", "name": "What Are You Watching", "examples": ["What are you watching?", "What's on your radar?", "Anything ahead?"]},
            {"id": "AI-002", "name": "What Changed", "examples": ["What changed?", "Anything different?", "What changed since last scan?"]},
            {"id": "AI-003", "name": "Biggest Concern", "examples": ["What worries you?", "Biggest risk?", "Should I be worried?"]},
            {"id": "AI-004", "name": "Explain Decision", "examples": ["Explain why", "Why did you say that?", "Show your reasoning"]},
            {"id": "AI-005", "name": "Would You Drive", "examples": ["Would you drive?", "Would you let your family drive?", "Would you cancel?"]},
            {"id": "AI-006", "name": "Tell Me What I Missed", "examples": ["What am I forgetting?", "Tell me something important", "What haven't I asked?"]},
            {"id": "AI-007", "name": "Keep Watching", "examples": ["Keep watching", "Wake me if it changes", "Monitor this trip"]},
            {"id": "AI-008", "name": "General Companion", "examples": ["Talk to me", "Tell me about this town", "Keep me company"]},
        ],
    },
]


def all_skills() -> List[Dict[str, Any]]:
    skills: List[Dict[str, Any]] = []
    for domain in WATCHMAN_SKILL_DOMAINS:
        for skill in domain.get("skills", []):
            row = dict(skill)
            row["domainId"] = domain["domainId"]
            row["domain"] = domain["name"]
            skills.append(row)
    return skills


def registry_summary() -> Dict[str, Any]:
    skills = all_skills()
    example_count = sum(len(s.get("examples", [])) for s in skills)
    return {
        "ok": True,
        "mode": "ChapNetAI Watchman Skills Registry V1",
        "domainCount": len(WATCHMAN_SKILL_DOMAINS),
        "skillCount": len(skills),
        "examplePhraseCount": example_count,
        "domains": WATCHMAN_SKILL_DOMAINS,
    }


def classify_question(question: str) -> Dict[str, Any]:
    q = (question or "").strip().lower()
    if not q:
        return {"ok": False, "error": "question_required"}

    best = None
    best_score = 0

    for skill in all_skills():
        score = 0
        haystack = " ".join([skill.get("name", ""), *skill.get("examples", [])]).lower()
        for token in q.replace("?", " ").replace(",", " ").split():
            if len(token) >= 3 and token in haystack:
                score += 1
        for phrase in skill.get("examples", []):
            phrase_l = phrase.lower().replace("?", "")
            if phrase_l and phrase_l in q:
                score += 5
        if score > best_score:
            best = skill
            best_score = score

    if not best:
        best = {
            "id": "AI-008",
            "name": "General Companion",
            "domainId": "AI",
            "domain": "Watchman AI Companion",
            "examples": [],
        }

    return {
        "ok": True,
        "question": question,
        "matchedSkill": best,
        "confidence": min(100, best_score * 15 if best_score else 35),
    }
