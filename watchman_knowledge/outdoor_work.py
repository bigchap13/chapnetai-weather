def outdoor_work_intelligence(weather):
    weather = weather or {}
    w = weather.get("watchman") or {}
    intel = w.get("liveStormIntelligence") or {}
    storm = w.get("stormTracker") or {}

    outdoor = int(w.get("outdoorIndex", 0) or 0)

    storm_active = storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"
    heat_active = intel.get("heatSignal") == "detected"
    flood_active = intel.get("floodSignal") == "detected"

    jobs = {}

    for job in [
        "roofing",
        "concrete",
        "painting",
        "landscaping",
        "mowing",
        "tree work",
        "pressure washing",
        "construction",
        "excavation",
    ]:
        score = outdoor

        if storm_active:
            score -= 40
        if heat_active:
            score -= 20
        if flood_active:
            score -= 20

        score = max(0, min(100, score))

        if score >= 75:
            verdict = "GO"
        elif score >= 45:
            verdict = "CAUTION"
        else:
            verdict = "DELAY"

        jobs[job] = {
            "verdict": verdict,
            "score": score,
        }

    return {
        "mode": "Watchman Outdoor Work Intelligence",
        "confidence": 88,
        "jobs": jobs,
    }
