def winter_road_intelligence(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    w = weather.get("watchman") or {}

    text = " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:6] if isinstance(x, dict)
    ).lower()

    text += " " + " ".join(
        str(x.get("shortForecast", ""))
        for x in hourly[:12] if isinstance(x, dict)
    ).lower()

    winter_signal = any(k in text for k in ["snow", "ice", "sleet", "freezing rain", "wintry", "black ice", "frost"])
    temp_risk = False

    for h in hourly[:12]:
        try:
            if int(h.get("temperature")) <= 34:
                temp_risk = True
        except Exception:
            pass

    risks = []
    if winter_signal:
        risks.append("winter precipitation signal")
    if temp_risk:
        risks.append("near-freezing road temperature signal")

    score = int(w.get("travelIndex", 75) or 75)

    if winter_signal:
        score -= 45
    if temp_risk:
        score -= 25

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "NORMAL"
        recommendation = "No major winter road hazard is indicated."
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Use caution. Bridges, shaded roads, and elevated surfaces could become slick."
    else:
        verdict = "DELAY"
        recommendation = "Delay travel if possible until winter road risk improves."

    return {
        "mode": "Watchman Winter Road Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 78,
        "recommendation": recommendation,
        "risks": risks or ["no winter road signal detected"],
        "bridgeRule": "Bridges and overpasses freeze before regular roads.",
        "blackIceRule": "Black ice is hardest to see near freezing temperatures, especially before sunrise.",
        "whatWouldChangeTheAnswer": [
            "Temperature drops near freezing",
            "Snow or ice appears in forecast",
            "New winter weather advisory",
            "Road reports become available",
        ],
    }
