def allergy_pollen_intelligence(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []

    text = " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:5] if isinstance(x, dict)
    ).lower()

    text += " " + " ".join(
        str(x.get("shortForecast", ""))
        for x in hourly[:12] if isinstance(x, dict)
    ).lower()

    rain_signal = any(k in text for k in ["rain", "showers", "thunderstorm"])
    wind_signal = "wind" in text or "breezy" in text
    dry_signal = any(k in text for k in ["sunny", "clear", "dry"])

    risks = []

    score = 50

    if wind_signal:
        score += 20
        risks.append("wind can stir pollen and dust")
    if dry_signal:
        score += 15
        risks.append("dry weather can allow pollen to stay airborne")
    if rain_signal:
        score -= 15
        risks.append("rain may temporarily reduce airborne pollen")

    score = max(0, min(100, score))

    if score >= 70:
        verdict = "HIGH"
        recommendation = "Allergy-sensitive users should consider limiting exposure and keeping windows closed."
    elif score >= 45:
        verdict = "MODERATE"
        recommendation = "Allergy conditions may bother sensitive users."
    else:
        verdict = "LOW"
        recommendation = "Weather pattern suggests lower airborne pollen pressure."

    return {
        "mode": "Watchman Allergy and Pollen Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 65,
        "recommendation": recommendation,
        "risks": risks or ["no strong pollen weather signal detected"],
        "guidance": [
            "Keep windows closed during high pollen periods.",
            "Shower after extended outdoor exposure.",
            "Use vehicle recirculation during high pollen or smoke periods.",
        ],
        "whatWouldChangeTheAnswer": [
            "Dedicated pollen data integration",
            "Rain timing changes",
            "Wind increases",
            "Dry weather persists",
        ],
    }
