from datetime import datetime


def _hour_from_time(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).hour
    except Exception:
        return None


def sunrise_sunset_intelligence(weather):
    weather = weather or {}
    hourly = weather.get("hourly") or []

    daylight_rows = []
    for h in hourly[:24]:
        if not isinstance(h, dict):
            continue
        hour = _hour_from_time(h.get("startTime"))
        short = str(h.get("shortForecast") or "")
        if hour is None:
            continue

        if 6 <= hour <= 8:
            period = "sunrise window"
        elif 17 <= hour <= 20:
            period = "sunset window"
        elif 9 <= hour <= 16:
            period = "daylight"
        else:
            period = "darkness"

        daylight_rows.append({
            "time": h.get("startTime"),
            "period": period,
            "conditions": short,
            "temperature": h.get("temperature"),
            "wind": h.get("windSpeed"),
        })

    sunrise_window = [r for r in daylight_rows if r["period"] == "sunrise window"]
    sunset_window = [r for r in daylight_rows if r["period"] == "sunset window"]

    return {
        "mode": "Watchman Sunrise Sunset Intelligence",
        "confidence": 70,
        "sunriseWindow": sunrise_window[:3],
        "sunsetWindow": sunset_window[:4],
        "daylightTimeline": daylight_rows,
        "recommendation": "Use sunrise and sunset windows for outdoor planning, photography, travel, and heat avoidance.",
        "note": "This V1 estimates daylight windows from hourly forecast time blocks. Dedicated astronomy API can improve exact sunrise and sunset times later.",
        "whatWouldChangeTheAnswer": [
            "dedicated sunrise/sunset API integration",
            "cloud cover changes",
            "fog forecast changes",
            "storm timing changes",
        ],
    }


def uv_intelligence(weather):
    weather = weather or {}
    hourly = weather.get("hourly") or []
    forecast = weather.get("forecast") or []

    text = " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:4] if isinstance(x, dict)
    ).lower()

    clear_signal = any(k in text for k in ["sunny", "clear", "mostly sunny", "partly sunny"])
    cloud_signal = any(k in text for k in ["cloudy", "overcast", "rain", "showers", "thunderstorm"])

    peak_hours = []
    for h in hourly[:24]:
        if not isinstance(h, dict):
            continue
        hour = _hour_from_time(h.get("startTime"))
        if hour is not None and 10 <= hour <= 16:
            peak_hours.append({
                "time": h.get("startTime"),
                "conditions": h.get("shortForecast"),
                "temperature": h.get("temperature"),
            })

    score = 55
    risks = []

    if clear_signal:
        score += 25
        risks.append("clear or sunny wording increases UV concern")
    if cloud_signal:
        score -= 15
        risks.append("clouds or rain may reduce direct UV exposure but do not eliminate it")
    if peak_hours:
        score += 10
        risks.append("midday peak UV window exists in the forecast timeline")

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "HIGH"
        recommendation = "Use sunscreen, shade, hat, sunglasses, and limit long midday exposure."
    elif score >= 45:
        verdict = "MODERATE"
        recommendation = "Use sun protection during midday outdoor activity."
    else:
        verdict = "LOWER"
        recommendation = "UV concern is lower, but sun protection can still matter."

    return {
        "mode": "Watchman UV Intelligence",
        "verdict": verdict,
        "score": score,
        "confidence": 68,
        "recommendation": recommendation,
        "risks": risks or ["no strong UV weather signal detected"],
        "peakWindow": peak_hours[:7],
        "sunburnRule": "Highest sunburn risk is usually late morning through afternoon.",
        "whatWouldChangeTheAnswer": [
            "dedicated UV index API integration",
            "cloud cover changes",
            "time of day",
            "season and sun angle",
        ],
    }
