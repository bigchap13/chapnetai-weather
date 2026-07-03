def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _text_blob(weather):
    weather = weather or {}
    parts = []

    for key in ["alerts", "forecast", "hourly"]:
        for item in weather.get(key, []) or []:
            if isinstance(item, dict):
                parts.extend(str(v) for v in item.values() if isinstance(v, (str, int, float)))

    watchman = weather.get("watchman") or {}
    for value in watchman.values():
        if isinstance(value, (str, int, float)):
            parts.append(str(value))

    return " ".join(parts).lower()


def radar_intelligence_v2(question, weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}
    alerts = weather.get("alerts") or []
    hourly = weather.get("hourly") or []

    text = _text_blob(weather)

    storm_detected = (
        storm.get("nearestStorm") == "Detected"
        or intel.get("stormSignal") == "detected"
        or "thunderstorm" in text
        or "lightning" in text
        or "severe thunderstorm" in text
    )

    score = 20
    signals = []

    if storm_detected:
        score += 45
        signals.append("storm or lightning signal detected")

    if alerts:
        score += 20
        signals.append(f"{len(alerts)} active alert(s)")

    if "severe thunderstorm" in text:
        score += 20
        signals.append("severe thunderstorm wording detected")

    if "tornado" in text:
        score += 35
        signals.append("tornado wording detected")

    if "hail" in text:
        score += 15
        signals.append("hail wording detected")

    if "damaging wind" in text or "wind advisory" in text:
        score += 15
        signals.append("wind impact wording detected")

    score = max(0, min(100, score))

    arrival = "unknown"
    for idx, h in enumerate(hourly[:8]):
        if not isinstance(h, dict):
            continue
        short = str(h.get("shortForecast") or "").lower()
        if "storm" in short or "thunderstorm" in short or "showers" in short:
            if idx == 0:
                arrival = "now or already nearby"
            elif idx == 1:
                arrival = "about 1 hour"
            else:
                arrival = f"about {idx} hours"
            break

    if score >= 75:
        verdict = "HIGH"
        recommendation = "Treat radar/storm risk as active. Stay weather-aware and be ready to shelter."
    elif score >= 45:
        verdict = "MONITOR"
        recommendation = "Storm signals are present. Keep Watchman open and watch for timing changes."
    else:
        verdict = "LOW"
        recommendation = "No strong radar/storm signal is detected from current Watchman inputs."

    return {
        "mode": "Watchman Radar Intelligence V2",
        "verdict": verdict,
        "score": score,
        "arrivalEstimate": arrival,
        "confidence": 78,
        "signals": signals or ["no strong radar/storm signal detected"],
        "recommendation": recommendation,
        "stormTracker": storm,
        "answer": (
            f"Radar Intelligence V2: {verdict} ({score}/100). "
            f"Arrival estimate: {arrival}. {recommendation} "
            f"Signals: {'; '.join(signals or ['no strong radar/storm signal detected'])}."
        ),
        "note": "V2 estimates radar/storm risk from Watchman storm signals, alerts, forecast wording, and hourly timing. Live radar motion-vector ingestion is the next phase.",
    }
