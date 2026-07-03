def air_quality_smoke_intelligence(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    w = weather.get("watchman") or {}
    intel = w.get("liveStormIntelligence") or {}

    text = " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:5] if isinstance(x, dict)
    ).lower()

    text += " " + " ".join(
        str(x.get("shortForecast", ""))
        for x in hourly[:12] if isinstance(x, dict)
    ).lower()

    smoke_signal = any(k in text for k in ["smoke", "haze", "wildfire", "air quality", "dust"])
    heat_signal = intel.get("heatSignal") == "detected" or "hot" in text or "heat" in text

    risks = []
    if smoke_signal:
        risks.append("smoke, haze, dust, or air-quality wording appears in forecast data")
    if heat_signal:
        risks.append("heat may worsen air-quality stress for sensitive groups")

    score = 100
    if smoke_signal:
        score -= 45
    if heat_signal:
        score -= 15

    score = max(0, min(100, score))

    if score >= 80:
        verdict = "GOOD"
        recommendation = "Air-quality stress is not a major Watchman signal right now."
    elif score >= 55:
        verdict = "CAUTION"
        recommendation = "Sensitive groups should reduce long outdoor exposure."
    else:
        verdict = "LIMIT OUTDOOR EXPOSURE"
        recommendation = "Limit strenuous outdoor activity, especially for sensitive groups."

    return {
        "mode": "Watchman Air Quality and Smoke Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 72,
        "recommendation": recommendation,
        "risks": risks or ["no major smoke or air-quality signal detected in current weather text"],
        "sensitiveGroups": [
            "children",
            "elderly people",
            "people with asthma",
            "people with heart or lung disease",
            "outdoor workers",
        ],
        "whatWouldChangeTheAnswer": [
            "AQI data integration",
            "smoke or haze appears in forecast",
            "wildfire smoke advisory",
            "wind direction changes",
            "heat increases",
        ],
    }
