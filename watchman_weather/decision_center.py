def _watchman(weather):
    return (weather or {}).get("watchman") or {}


def _storm_active(weather):
    w = _watchman(weather)
    storm = w.get("stormTracker") or {}
    intel = w.get("liveStormIntelligence") or {}
    return storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"


def _heat_active(weather):
    w = _watchman(weather)
    intel = w.get("liveStormIntelligence") or {}
    return intel.get("heatSignal") == "detected"


def _flood_active(weather):
    w = _watchman(weather)
    intel = w.get("liveStormIntelligence") or {}
    return intel.get("floodSignal") == "detected"


def _extract_activity(question):
    q = str(question or "").lower()
    activities = {
        "mow": ["mow", "cut grass", "yard"],
        "grill": ["grill", "bbq", "barbecue"],
        "drive": ["drive", "travel", "road trip", "leave"],
        "walk dog": ["walk dog", "dog walk"],
        "kids outside": ["kids outside", "children outside", "play outside"],
        "pets outside": ["pets outside", "dog outside", "cat outside"],
        "roof": ["roof", "roofing"],
        "concrete": ["concrete", "pour concrete"],
        "crane": ["crane", "lift"],
        "fish": ["fish", "fishing"],
        "boat": ["boat", "boating"],
        "hike": ["hike", "hiking"],
        "golf": ["golf", "golfing"],
        "wash car": ["wash car", "car wash"],
        "camp": ["camp", "camping"],
        "swim": ["swim", "swimming", "pool"],
    }
    for activity, keys in activities.items():
        if any(k in q for k in keys):
            return activity
    return None


def decision_center(question, weather):
    weather = weather or {}
    w = _watchman(weather)

    activity = _extract_activity(question)
    if not activity:
        return None

    outdoor = int(w.get("outdoorIndex", 0) or 0)
    travel = int(w.get("travelIndex", 0) or 0)
    storm = _storm_active(weather)
    heat = _heat_active(weather)
    flood = _flood_active(weather)

    reasons = []
    do_now = []
    avoid = []
    safe_window = "No clear safe window identified yet."
    change_answer = []

    if storm:
        reasons.append("storm or lightning signal is active")
        avoid.append("Avoid exposed outdoor activity while thunder or lightning is possible.")
        do_now.append("Keep radar and alerts open.")
        change_answer.append("Storm signal clears or radar shows storms moving away.")

    if heat:
        reasons.append("heat risk is active")
        avoid.append("Avoid peak afternoon heat if possible.")
        do_now.append("Hydrate and take shade or cooling breaks.")
        change_answer.append("Heat index drops or the activity can move to morning/evening.")

    if flood:
        reasons.append("flooding signal is active")
        avoid.append("Avoid low-water crossings and poor-drainage roads.")
        change_answer.append("Flood signal clears and roads remain passable.")

    if outdoor < 40 and activity not in ["drive"]:
        reasons.append("outdoor index is low")

    if travel < 40 and activity == "drive":
        reasons.append("travel index is low")

    high_risk_activities = {"roof", "crane", "boat", "swim", "camp", "hike", "kids outside", "pets outside", "walk dog"}
    heat_sensitive = {"mow", "roof", "concrete", "kids outside", "pets outside", "walk dog", "hike", "golf"}

    if storm and activity in high_risk_activities:
        verdict = "NO"
        confidence = 92
    elif heat and activity in heat_sensitive:
        verdict = "CAUTION" if outdoor >= 45 else "NO"
        confidence = 88
    elif flood and activity in ["drive", "fish", "boat", "camp"]:
        verdict = "NO"
        confidence = 90
    elif outdoor >= 70 and travel >= 70:
        verdict = "YES"
        confidence = 84
    elif outdoor >= 45:
        verdict = "CAUTION"
        confidence = 78
    else:
        verdict = "NO"
        confidence = 80

    if verdict == "YES":
        recommendation = f"Yes, {activity} looks reasonable based on the current Watchman scan."
        safe_window = "Current window looks usable. Recheck before starting."
    elif verdict == "CAUTION":
        recommendation = f"Use caution with {activity}. Conditions are not ideal."
        safe_window = "Short window only. Recheck radar and alerts before starting."
    else:
        recommendation = f"No, delay {activity} if possible."
        safe_window = "Wait until storm, heat, or hazard signals improve."

    if not reasons:
        reasons.append("no major Watchman hazard signal is active")

    if not do_now:
        do_now.append("Recheck Watchman before starting.")

    if not avoid:
        avoid.append("Avoid ignoring sudden weather changes.")

    if not change_answer:
        change_answer.append("New alerts, radar changes, or forecast changes could change this recommendation.")

    return {
        "activity": activity,
        "verdict": verdict,
        "recommendation": recommendation,
        "confidence": confidence,
        "reasoning": reasons,
        "doNow": do_now,
        "avoid": avoid,
        "safeWindow": safe_window,
        "whatWouldChangeTheAnswer": change_answer,
    }
