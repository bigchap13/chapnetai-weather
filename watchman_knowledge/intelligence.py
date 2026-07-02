def _clamp(value, low=0, high=100):
    try:
        value = int(value)
    except Exception:
        value = 0
    return max(low, min(high, value))


def _combined_text(weather):
    weather = weather or {}
    alerts = weather.get("alerts") or []
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    watchman = weather.get("watchman") or {}

    parts = []

    for alert in alerts:
        if isinstance(alert, dict):
            parts.extend([
                str(alert.get("event", "")),
                str(alert.get("headline", "")),
                str(alert.get("description", "")),
                str(alert.get("instruction", "")),
            ])

    for item in forecast[:6]:
        if isinstance(item, dict):
            parts.extend([
                str(item.get("name", "")),
                str(item.get("shortForecast", "")),
                str(item.get("detailedForecast", "")),
            ])

    for item in hourly[:12]:
        if isinstance(item, dict):
            parts.extend([
                str(item.get("shortForecast", "")),
                str(item.get("windSpeed", "")),
            ])

    parts.extend([
        str(watchman.get("aiBriefing", "")),
        str(watchman.get("aiWeatherNarrative", "")),
    ])

    return " ".join(parts).lower()


def build_hazard_board(weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    text = _combined_text(weather)

    score = _clamp(watchman.get("threatScore", 0))
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}

    lightning = 15
    wind = 10
    flood = 10
    heat = 10
    tornado = 5
    hail = 5

    if "lightning" in text or "thunderstorm" in text:
        lightning += 55
    if "severe thunderstorm" in text or "damaging wind" in text or "high wind" in text:
        wind += 55
    if "flood" in text or intel.get("floodSignal") == "detected":
        flood += 55
    if "heat advisory" in text or "heat index" in text or intel.get("heatSignal") == "detected":
        heat += 65
    if "tornado warning" in text:
        tornado += 90
    elif "tornado watch" in text or "rotation" in text:
        tornado += 55
    if "hail" in text:
        hail += 50

    if storm.get("nearestStorm") == "Detected":
        lightning += 15
        wind += 10

    hazards = [
        {"name": "Lightning", "score": _clamp(lightning), "level": _level(lightning)},
        {"name": "Damaging Wind", "score": _clamp(wind), "level": _level(wind)},
        {"name": "Flash Flood", "score": _clamp(flood), "level": _level(flood)},
        {"name": "Heat Stress", "score": _clamp(heat), "level": _level(heat)},
        {"name": "Tornado", "score": _clamp(tornado), "level": _level(tornado)},
        {"name": "Large Hail", "score": _clamp(hail), "level": _level(hail)},
    ]

    hazards.sort(key=lambda x: x["score"], reverse=True)

    return {
        "overallThreatScore": score,
        "hazards": hazards,
        "topHazard": hazards[0],
    }


def _level(score):
    score = _clamp(score)
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "elevated"
    if score > 0:
        return "guarded"
    return "normal"


def tornado_intelligence(weather):
    text = _combined_text(weather)

    if "tornado warning" in text:
        status = "warning"
        action = "Shelter immediately in an interior room on the lowest floor."
        confidence = 96
    elif "tornado watch" in text:
        status = "watch"
        action = "Stay ready to shelter. Conditions are favorable for tornado development."
        confidence = 88
    elif "rotation" in text or "supercell" in text:
        status = "rotation_possible"
        action = "Monitor radar and official NWS alerts closely."
        confidence = 72
    elif "severe thunderstorm" in text:
        status = "low_but_monitor"
        action = "Tornado risk is not the lead signal, but severe storms should be watched."
        confidence = 61
    else:
        status = "not_indicated"
        action = "No tornado signal detected in the current Watchman scan."
        confidence = 55

    return {
        "status": status,
        "action": action,
        "confidence": confidence,
        "shelterRule": "Lowest floor, interior room, away from windows.",
    }


def heat_index_intelligence(weather):
    weather = weather or {}
    obs = weather.get("observation") or {}
    forecast = weather.get("forecast") or []
    text = _combined_text(weather)

    temp = obs.get("temperatureF")
    if temp is None and forecast:
        temp = forecast[0].get("temperature")

    heat_signal = "heat advisory" in text or "heat index" in text or "hot" in text

    try:
        temp_num = int(temp)
    except Exception:
        temp_num = None

    if heat_signal and temp_num and temp_num >= 95:
        risk = "high"
        action = "Limit heavy outdoor work. Take cooling breaks every 15 to 20 minutes."
        confidence = 88
    elif heat_signal:
        risk = "elevated"
        action = "Hydrate often and reduce exposure during peak heat."
        confidence = 80
    elif temp_num and temp_num >= 92:
        risk = "elevated"
        action = "Heat stress is possible during long outdoor activity."
        confidence = 70
    else:
        risk = "normal"
        action = "No major heat stress signal detected."
        confidence = 60

    return {
        "risk": risk,
        "temperatureF": temp_num,
        "action": action,
        "confidence": confidence,
        "vehicleWarning": "Never leave children or pets in a parked vehicle.",
        "petWarning": "If pavement is too hot for your hand, it is too hot for paws.",
    }


def predictive_timeline(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []
    watchman = weather.get("watchman") or {}
    storm = watchman.get("stormTracker") or {}
    hazards = build_hazard_board(weather)["hazards"]

    timeline = []

    first = forecast[0] if forecast else {}
    second = forecast[1] if len(forecast) > 1 else {}

    timeline.append({
        "time": "Now",
        "event": first.get("shortForecast") or "Conditions updating",
        "risk": hazards[0]["level"],
    })

    timeline.append({
        "time": "Next window",
        "event": storm.get("estimatedArrival") or "No organized storm arrival signal.",
        "risk": storm.get("intensity") or "unknown",
    })

    if second:
        timeline.append({
            "time": second.get("name") or "Later",
            "event": second.get("shortForecast") or "Forecast updating",
            "risk": "monitor",
        })

    timeline.append({
        "time": "Watchman focus",
        "event": "Primary hazard: " + hazards[0]["name"],
        "risk": hazards[0]["level"],
    })

    return timeline


def intelligence_summary(weather):
    board = build_hazard_board(weather)
    tornado = tornado_intelligence(weather)
    heat = heat_index_intelligence(weather)
    timeline = predictive_timeline(weather)

    return {
        "hazardBoard": board,
        "tornadoIntelligence": tornado,
        "heatIndexIntelligence": heat,
        "predictiveTimeline": timeline,
        "summary": (
            "Watchman Intelligence V2 is evaluating hazard ranking, tornado risk, "
            "heat stress, and the next likely weather change."
        ),
    }
