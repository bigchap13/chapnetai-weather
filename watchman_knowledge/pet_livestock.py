def pet_livestock_intelligence(weather):
    weather = weather or {}
    w = weather.get("watchman") or {}
    obs = weather.get("observation") or {}
    forecast = weather.get("forecast") or []
    storm = w.get("stormTracker") or {}
    intel = w.get("liveStormIntelligence") or {}

    first = forecast[0] if forecast and isinstance(forecast[0], dict) else {}

    temp = obs.get("temperatureF") or first.get("temperature") or 0
    try:
        temp = int(temp)
    except Exception:
        temp = 0

    storm_active = storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"
    heat_active = intel.get("heatSignal") == "detected" or temp >= 90
    flood_active = intel.get("floodSignal") == "detected"

    risks = []

    if storm_active:
        risks.append("lightning/thunder risk")
    if heat_active:
        risks.append("heat stress and pavement burn risk")
    if flood_active:
        risks.append("flooded ground or unsafe crossings")

    score = 100
    if storm_active:
        score -= 40
    if heat_active:
        score -= 35
    if flood_active:
        score -= 25

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "SAFE"
        recommendation = "Normal caution is enough."
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Limit time outside and monitor conditions."
    else:
        verdict = "KEEP INSIDE"
        recommendation = "Keep pets or vulnerable livestock sheltered if possible."

    return {
        "mode": "Watchman Pet and Livestock Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 87,
        "recommendation": recommendation,
        "risks": risks or ["no major pet or livestock hazard detected"],
        "dogWalkGuidance": "Use short walks, shade, water, and avoid hot pavement.",
        "livestockGuidance": "Check water, shade, ventilation, and storm shelter access.",
        "vehicleWarning": "Never leave pets or children in a parked vehicle.",
        "whatWouldChangeTheAnswer": [
            "Temperature drops",
            "Storm signal clears",
            "Flood signal clears",
            "New NWS warning",
        ],
    }
