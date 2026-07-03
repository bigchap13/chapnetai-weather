from datetime import datetime


def _hour_from_time(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).hour
    except Exception:
        return None


def astronomy_intelligence(weather):
    weather = weather or {}
    hourly = weather.get("hourly") or []
    forecast = weather.get("forecast") or []

    text = " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:4] if isinstance(x, dict)
    ).lower()

    cloud_signal = any(k in text for k in ["cloudy", "overcast", "rain", "showers", "thunderstorm", "fog"])
    clear_signal = any(k in text for k in ["clear", "mostly clear", "sunny"])

    night_rows = []
    for h in hourly[:24]:
        if not isinstance(h, dict):
            continue
        hour = _hour_from_time(h.get("startTime"))
        if hour is not None and (hour >= 20 or hour <= 5):
            night_rows.append({
                "time": h.get("startTime"),
                "conditions": h.get("shortForecast"),
                "temperature": h.get("temperature"),
                "wind": h.get("windSpeed"),
            })

    score = 60
    risks = []

    if clear_signal:
        score += 25
        risks.append("clear-sky wording supports sky viewing")
    if cloud_signal:
        score -= 35
        risks.append("clouds, fog, rain, or storms may block sky visibility")
    if not night_rows:
        risks.append("night forecast window is limited")

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "GOOD"
        recommendation = "Sky viewing looks usable if local light pollution is low."
    elif score >= 45:
        verdict = "FAIR"
        recommendation = "Sky viewing may be possible, but clouds or storms could interfere."
    else:
        verdict = "POOR"
        recommendation = "Astronomy viewing is not favored by current forecast signals."

    return {
        "mode": "Watchman Astronomy Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 67,
        "recommendation": recommendation,
        "risks": risks or ["no major astronomy issue detected"],
        "nightWindow": night_rows[:8],
        "guidance": [
            "Best viewing usually needs clear sky, low haze, low moonlight, and low light pollution.",
            "Check the sky again near sunset because cloud timing can change quickly.",
        ],
        "whatWouldChangeTheAnswer": [
            "dedicated moon phase integration",
            "cloud forecast changes",
            "fog forecast changes",
            "storm timing changes",
            "smoke or haze changes",
        ],
    }


def fire_weather_intelligence(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    alerts = weather.get("alerts") or []

    text = " ".join(
        str(x.get("event", "")) + " " + str(x.get("headline", ""))
        for x in alerts if isinstance(x, dict)
    ).lower()

    text += " " + " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:5] if isinstance(x, dict)
    ).lower()

    wind_signal = False
    dry_signal = any(k in text for k in ["dry", "red flag", "fire weather", "low humidity", "wind advisory"])
    rain_signal = any(k in text for k in ["rain", "showers", "thunderstorm"])

    for h in hourly[:12]:
        wind = str(h.get("windSpeed", "")).lower()
        try:
            number = int("".join(ch if ch.isdigit() else " " for ch in wind).split()[0])
            if number >= 15:
                wind_signal = True
        except Exception:
            pass

    risks = []

    if dry_signal:
        risks.append("dry/fire-weather wording appears in forecast or alert data")
    if wind_signal:
        risks.append("wind may increase fire spread risk")
    if rain_signal:
        risks.append("rain or storm chances may reduce fire risk but lightning can still matter")

    score = 25
    if dry_signal:
        score += 40
    if wind_signal:
        score += 25
    if rain_signal:
        score -= 10

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "HIGH"
        recommendation = "Avoid outdoor burning. Fire spread risk may be elevated."
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Use caution with fire, grills, sparks, welding, and debris burning."
    else:
        verdict = "LOWER"
        recommendation = "No major fire-weather signal is detected, but follow local burn rules."

    return {
        "mode": "Watchman Fire Weather Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 72,
        "recommendation": recommendation,
        "risks": risks or ["no major fire-weather signal detected"],
        "burnRule": "Always follow local burn bans and fire department guidance.",
        "sparkRule": "Wind, dry fuels, and low humidity can turn small sparks into fast-spreading fires.",
        "whatWouldChangeTheAnswer": [
            "red flag warning",
            "wind increase",
            "humidity decrease",
            "rain timing changes",
            "local burn ban integration",
        ],
    }
