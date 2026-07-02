def activity_decision(question, weather):
    q = str(question or "").lower()
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    outdoor = int(watchman.get("outdoorIndex", 0) or 0)
    travel = int(watchman.get("travelIndex", 0) or 0)
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}

    storm_active = storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"
    heat_active = intel.get("heatSignal") == "detected"
    flood_active = intel.get("floodSignal") == "detected"

    activity = None
    for item in ["mow", "grill", "hike", "fish", "boat", "swim", "golf", "wash", "camp", "drive", "roof", "concrete", "crane", "walk dog", "kids outside", "pets"]:
        if item in q:
            activity = item
            break

    if not activity:
        return None

    reasons = []

    if storm_active:
        reasons.append("storm or lightning signal is active")
    if heat_active:
        reasons.append("heat risk is active")
    if flood_active:
        reasons.append("flooding signal is active")
    if outdoor < 40:
        reasons.append("outdoor index is low")
    if travel < 40 and activity == "drive":
        reasons.append("travel index is low")

    if storm_active or outdoor < 35 or (activity == "drive" and travel < 40):
        verdict = "NO"
        recommendation = "Delay if possible."
    elif heat_active or outdoor < 65:
        verdict = "CAUTION"
        recommendation = "You can do it, but shorten the activity and keep Watchman open."
    else:
        verdict = "YES"
        recommendation = "Conditions look usable."

    if not reasons:
        reasons.append("no major Watchman hazard signal is active")

    return {
        "activity": activity,
        "verdict": verdict,
        "recommendation": recommendation,
        "confidence": 88 if reasons else 70,
        "reasons": reasons,
    }
