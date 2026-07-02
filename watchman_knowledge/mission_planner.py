def _watchman(weather):
    return (weather or {}).get("watchman") or {}


def _forecast(weather):
    return (weather or {}).get("forecast") or []


def _hourly(weather):
    return (weather or {}).get("hourly") or []


def _detect_mission(text):
    q = str(text or "").lower()

    missions = {
        "commute": ["work", "commute", "drive", "leave", "road", "trip"],
        "grilling": ["grill", "bbq", "barbecue", "cookout"],
        "sports": ["soccer", "football", "baseball", "practice", "game"],
        "concrete": ["concrete", "pour concrete"],
        "roofing": ["roof", "roofing"],
        "hiking": ["hike", "hiking", "trail"],
        "camping": ["camp", "camping"],
        "motorcycle": ["motorcycle", "bike ride"],
        "drone": ["drone", "fly drone"],
        "boating": ["boat", "boating", "lake"],
        "fishing": ["fish", "fishing"],
        "pets": ["dog", "pet", "pets", "livestock"],
        "kids": ["kids", "children", "school", "recess"],
        "farm": ["farm", "spray", "hay", "livestock", "irrigation"],
    }

    for mission, words in missions.items():
        if any(w in q for w in words):
            return mission

    return "general"


def _risk_from_hour(hour):
    text = str(hour.get("shortForecast") or "").lower()
    temp = hour.get("temperature")
    pop = ((hour.get("probabilityOfPrecipitation") or {}).get("value"))

    risks = []

    if "thunderstorm" in text or "storm" in text:
        risks.append("storm")
    if "showers" in text or "rain" in text:
        risks.append("rain")
    if "fog" in text:
        risks.append("visibility")
    if temp is not None:
        try:
            if int(temp) >= 92:
                risks.append("heat")
        except Exception:
            pass
    if pop is not None:
        try:
            if int(pop) >= 40:
                risks.append("precipitation")
        except Exception:
            pass

    return risks or ["normal"]


def build_mission_plan(question, weather):
    weather = weather or {}
    mission = _detect_mission(question)
    w = _watchman(weather)
    hourly = _hourly(weather)

    storm = w.get("stormTracker") or {}
    intel = w.get("liveStormIntelligence") or {}

    storm_active = storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"
    heat_active = intel.get("heatSignal") == "detected"
    flood_active = intel.get("floodSignal") == "detected"

    timeline = []
    for h in hourly[:8]:
        if not isinstance(h, dict):
            continue
        timeline.append({
            "time": h.get("startTime"),
            "conditions": h.get("shortForecast"),
            "temperature": h.get("temperature"),
            "precipChance": ((h.get("probabilityOfPrecipitation") or {}).get("value")),
            "wind": h.get("windSpeed"),
            "risks": _risk_from_hour(h),
        })

    reasons = []
    if storm_active:
        reasons.append("storm or lightning signal is active")
    if heat_active:
        reasons.append("heat signal is active")
    if flood_active:
        reasons.append("flooding signal is active")

    outdoor = int(w.get("outdoorIndex", 0) or 0)
    travel = int(w.get("travelIndex", 0) or 0)

    if mission in ["commute", "motorcycle"]:
        base_score = travel
    else:
        base_score = outdoor

    if storm_active:
        base_score -= 35
    if heat_active and mission in ["sports", "concrete", "roofing", "hiking", "kids", "pets", "farm"]:
        base_score -= 25
    if flood_active and mission in ["commute", "boating", "fishing", "camping"]:
        base_score -= 30

    score = max(0, min(100, base_score))

    if score >= 75:
        verdict = "GO"
        recommendation = "Conditions look usable, but recheck Watchman before starting."
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Proceed only with monitoring and a backup plan."
    else:
        verdict = "DELAY"
        recommendation = "Delay this mission if possible."

    best_window = "Current window looks usable." if score >= 75 else "Wait for storm, heat, or hazard signals to improve."
    backup_window = "Use the next lower-risk hourly period shown in the mission timeline."

    if not reasons:
        reasons.append("no major Watchman hazard signal is active")

    checklist = [
        "Check radar before starting.",
        "Keep alerts enabled.",
        "Have a backup plan if conditions change.",
    ]

    if heat_active:
        checklist.append("Bring water and plan cooling breaks.")
    if storm_active:
        checklist.append("Know where you will shelter if thunder is heard.")
    if flood_active:
        checklist.append("Avoid low-water crossings and poor drainage roads.")

    return {
        "mode": "Watchman Mission Planner",
        "mission": mission,
        "verdict": verdict,
        "score": score,
        "confidence": 88,
        "recommendation": recommendation,
        "reasoning": reasons,
        "bestWindow": best_window,
        "backupWindow": backup_window,
        "checklist": checklist,
        "whatWouldChangeTheAnswer": [
            "New NWS alerts",
            "Radar changes",
            "Storm tracker changes",
            "Heat signal changes",
            "Hourly forecast update",
        ],
        "timeline": timeline,
    }
