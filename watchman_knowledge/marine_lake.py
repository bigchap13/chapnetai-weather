def marine_lake_intelligence(weather):
    weather = weather or {}
    w = weather.get("watchman") or {}
    hourly = weather.get("hourly") or []
    storm = w.get("stormTracker") or {}
    intel = w.get("liveStormIntelligence") or {}

    storm_active = storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected"
    flood_active = intel.get("floodSignal") == "detected"

    wind_risk = False
    rain_risk = False

    for h in hourly[:6]:
        text = str(h.get("shortForecast", "")).lower()
        wind = str(h.get("windSpeed", "")).lower()

        if "wind" in text or "mph" in wind:
            try:
                number = int("".join(ch if ch.isdigit() else " " for ch in wind).split()[0])
                if number >= 15:
                    wind_risk = True
            except Exception:
                pass

        if "rain" in text or "showers" in text or "thunderstorm" in text:
            rain_risk = True

    risks = []
    if storm_active:
        risks.append("lightning/storm risk on open water")
    if flood_active:
        risks.append("flood/current risk")
    if wind_risk:
        risks.append("wind/wave risk")
    if rain_risk:
        risks.append("reduced visibility or wet conditions")

    score = 100
    if storm_active:
        score -= 45
    if flood_active:
        score -= 30
    if wind_risk:
        score -= 20
    if rain_risk:
        score -= 15

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "GO"
        recommendation = "Lake or marine activity looks usable with normal caution."
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Use caution and stay close to safe shelter."
    else:
        verdict = "DO NOT LAUNCH"
        recommendation = "Delay boating, kayaking, swimming, or lake activity if possible."

    return {
        "mode": "Watchman Marine and Lake Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 84,
        "recommendation": recommendation,
        "risks": risks or ["no major lake hazard detected"],
        "lightningRule": "Get off the water immediately if thunder is heard.",
        "boatingRule": "Wear a life jacket and monitor wind, lightning, and visibility.",
        "whatWouldChangeTheAnswer": [
            "Storm signal clears",
            "Wind decreases",
            "Flood signal clears",
            "Radar shows storms moving away",
        ],
    }
