def event_intelligence(weather):
    weather = weather or {}
    w = weather.get("watchman") or {}
    intel = w.get("liveStormIntelligence") or {}
    storm = w.get("stormTracker") or {}

    outdoor = int(w.get("outdoorIndex", 0) or 0)

    storm_active = storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"
    heat_active = intel.get("heatSignal") == "detected"

    events = {}

    for event in [
        "wedding",
        "cookout",
        "festival",
        "ball game",
        "fireworks",
        "concert",
        "graduation",
        "church event",
        "school event",
        "birthday party",
    ]:
        score = outdoor

        if storm_active:
            score -= 35

        if heat_active:
            score -= 15

        score = max(0, min(100, score))

        if score >= 75:
            verdict = "GO"
        elif score >= 45:
            verdict = "CAUTION"
        else:
            verdict = "DELAY"

        events[event] = {
            "verdict": verdict,
            "score": score,
        }

    return {
        "mode": "Watchman Event Intelligence",
        "confidence": 87,
        "events": events,
    }
