def lightning_intelligence(question, weather):
    weather = weather or {}
    w = weather.get("watchman") or {}
    storm = w.get("stormTracker") or {}
    intel = w.get("liveStormIntelligence") or {}
    forecast = weather.get("forecast") or []

    text = " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:4] if isinstance(x, dict)
    ).lower()

    signal = (
        storm.get("nearestStorm") == "Detected"
        or intel.get("stormSignal") == "detected"
        or "thunderstorm" in text
        or "lightning" in text
    )

    if signal:
        status = "active"
        risk = "elevated"
        action = "Stay indoors if thunder is heard. Wait at least 30 minutes after the last thunder before resuming outdoor activity."
        confidence = 84
    else:
        status = "not_detected"
        risk = "low"
        action = "No lightning signal is currently indicated by Watchman, but continue monitoring if storms are nearby."
        confidence = 68

    return {
        "mode": "Watchman Lightning Intelligence",
        "status": status,
        "risk": risk,
        "confidence": confidence,
        "action": action,
        "safetyRule": "When thunder roars, go indoors.",
        "returnOutsideRule": "Wait 30 minutes after the last thunder.",
        "whatWouldChangeTheAnswer": [
            "Thunderstorm forecast appears",
            "Storm tracker detects nearby storm",
            "NWS warning is issued",
            "Radar shows new development",
        ],
    }
