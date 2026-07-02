def travel_intelligence(question, weather):
    weather = weather or {}
    w = weather.get("watchman") or {}
    hourly = weather.get("hourly") or []
    alerts = weather.get("alerts") or []

    travel = int(w.get("travelIndex", 0) or 0)
    storm = w.get("stormTracker") or {}
    intel = w.get("liveStormIntelligence") or {}

    storm_active = storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"
    flood_active = intel.get("floodSignal") == "detected"

    hazards = []
    if storm_active:
        hazards.append("storm or lightning risk")
    if flood_active:
        hazards.append("flooding or poor drainage risk")
    if alerts:
        hazards.append(f"{len(alerts)} active NWS alert(s)")

    for h in hourly[:4]:
        text = str(h.get("shortForecast", "")).lower()
        if "fog" in text and "fog/visibility risk" not in hazards:
            hazards.append("fog/visibility risk")
        if "wind" in text and "wind impact risk" not in hazards:
            hazards.append("wind impact risk")
        if "rain" in text or "showers" in text or "thunderstorm" in text:
            if "wet-road risk" not in hazards:
                hazards.append("wet-road risk")

    score = travel
    if storm_active:
        score -= 30
    if flood_active:
        score -= 30
    if alerts:
        score -= 10

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "GO"
        recommendation = "Travel looks usable. Keep Watchman open before leaving."
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Travel is possible, but conditions may affect timing or visibility."
    else:
        verdict = "DELAY"
        recommendation = "Delay travel if possible until hazards improve."

    return {
        "mode": "Watchman Travel Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 86,
        "recommendation": recommendation,
        "hazards": hazards or ["no major travel hazard detected"],
        "bestDepartureWindow": "Leave during the lowest-risk hourly period shown by Watchman.",
        "backupDepartureWindow": "Delay until storm, flood, visibility, or alert signals improve.",
        "whatWouldChangeTheAnswer": [
            "New NWS warning",
            "Radar storm movement",
            "Flood signal",
            "Visibility reduction",
            "Wind increase",
        ],
    }
