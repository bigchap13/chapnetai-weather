def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _first_forecast(weather):
    forecast = (weather or {}).get("forecast") or []
    return forecast[0] if forecast and isinstance(forecast[0], dict) else {}


def _watchman(weather):
    return (weather or {}).get("watchman") or {}


def build_reasoning_answer(question, weather, direct_answer=None):
    weather = weather or {}
    question = question or ""
    watchman = _watchman(weather)
    first = _first_forecast(weather)
    obs = weather.get("observation") or {}
    alerts = weather.get("alerts") or []

    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}
    changed = watchman.get("whatChanged") or {}

    temp = obs.get("temperatureF") or first.get("temperature")
    condition = obs.get("text") or first.get("shortForecast") or "conditions are updating"
    pop = ((first.get("probabilityOfPrecipitation") or {}).get("value"))
    threat = watchman.get("threatLevel", "unknown")
    score = watchman.get("threatScore", "unknown")

    evidence = []
    evidence.append(f"Current condition: {condition}.")
    if temp is not None:
        evidence.append(f"Temperature: {temp}°F.")
    if pop is not None:
        evidence.append(f"Precipitation chance: {pop}%.")
    evidence.append(f"Watchman threat level: {threat} at {score}/100.")
    evidence.append(f"Active alerts: {len(alerts)}.")
    if storm:
        evidence.append(f"Storm tracker: {storm.get('nearestStorm', 'unknown')} / {storm.get('intensity', 'unknown')}.")
    if changed.get("changes"):
        evidence.append("Recent change: " + str(changed.get("changes")[0]))

    confidence = 70
    if alerts:
        confidence += 10
    if first:
        confidence += 8
    if obs:
        confidence += 7
    if storm:
        confidence += 5
    confidence = min(confidence, 96)

    analysis = "Watchman evaluated current observations, NWS forecast periods, active alerts, storm signals, and recent scan changes."
    prediction = storm.get("estimatedArrival") or "No organized storm arrival signal is currently detected."
    recommendation = direct_answer or watchman.get("aiWeatherNarrative") or watchman.get("aiBriefing") or "Continue monitoring Watchman updates."

    return {
        "question": question,
        "observation": evidence,
        "analysis": analysis,
        "prediction": prediction,
        "recommendation": recommendation,
        "confidence": confidence,
        "plainAnswer": (
            f"{recommendation} Confidence: {confidence}%. "
            f"Evidence: {' '.join(evidence[:4])}"
        ),
    }
