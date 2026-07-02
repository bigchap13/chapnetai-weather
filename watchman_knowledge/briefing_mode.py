def build_hourly_timeline(weather):
    weather = weather or {}
    hourly = weather.get("hourly") or []
    watchman = weather.get("watchman") or {}

    rows = []
    for h in hourly[:8]:
        if not isinstance(h, dict):
            continue

        pop = ((h.get("probabilityOfPrecipitation") or {}).get("value"))
        short = h.get("shortForecast") or "Conditions updating"
        temp = h.get("temperature")
        wind = h.get("windSpeed") or ""

        risk = "normal"
        text = short.lower()
        if "thunderstorm" in text or "storm" in text:
            risk = "storm"
        elif "rain" in text or "showers" in text:
            risk = "rain"
        elif temp is not None and int(temp) >= 92:
            risk = "heat"
        elif "fog" in text:
            risk = "visibility"

        rows.append({
            "time": h.get("startTime"),
            "conditions": short,
            "temperature": temp,
            "precipChance": pop,
            "wind": wind,
            "risk": risk,
        })

    if not rows:
        rows.append({
            "time": "Now",
            "conditions": "Hourly data unavailable.",
            "temperature": None,
            "precipChance": None,
            "wind": "",
            "risk": "unknown",
        })

    return rows


def build_watchman_briefing(weather):
    weather = weather or {}
    location = weather.get("location") or {}
    place = location.get("name") or "this location"

    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    forecast = weather.get("forecast") or []

    first = forecast[0] if forecast and isinstance(forecast[0], dict) else {}
    storm = watchman.get("stormTracker") or {}
    changed = watchman.get("whatChanged") or {}

    lines = [
        f"Watchman briefing for {place}.",
        f"Current threat level is {watchman.get('threatLevel', 'unknown')} with a score of {watchman.get('threatScore', 'unknown')}/100.",
        f"Forecast window: {first.get('name', 'current period')} — {first.get('shortForecast', 'conditions updating')}.",
        f"Active alerts: {len(alerts)}.",
        f"Storm tracker: {storm.get('nearestStorm', 'unknown')} / {storm.get('intensity', 'unknown')}.",
        f"Arrival estimate: {storm.get('estimatedArrival', 'No organized storm arrival signal.')}",
        changed.get("summary", "No previous Watchman change summary available."),
    ]

    return {
        "mode": "Watchman Briefing Mode",
        "location": place,
        "briefing": " ".join(lines),
        "hourlyTimeline": build_hourly_timeline(weather),
    }
