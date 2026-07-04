def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def storm_arrival_engine(question, weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    hourly = weather.get("hourly") or []
    alerts = weather.get("alerts") or []

    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}

    storm_signal = (
        storm.get("nearestStorm") == "Detected"
        or intel.get("stormSignal") == "detected"
        or any("storm" in str(a).lower() or "thunder" in str(a).lower() for a in alerts)
    )

    arrival = "unknown"
    arrival_minutes = None
    confidence = 62

    for idx, h in enumerate(hourly[:12]):
        if not isinstance(h, dict):
            continue
        text = str(h.get("shortForecast") or "").lower()
        if "storm" in text or "thunder" in text or "showers" in text:
            if idx == 0:
                arrival = "now or already nearby"
                arrival_minutes = 0
            else:
                arrival = f"about {idx} hour(s)"
                arrival_minutes = idx * 60
            confidence = 78
            break

    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)

    if storm_signal and arrival == "unknown":
        arrival = storm.get("estimatedArrival") or "storms possible in the next forecast window"
        confidence = 68

    if threat >= 50:
        status = "approaching_or_nearby"
    elif storm_signal or precip >= 35:
        status = "possible"
    else:
        status = "not_detected"

    if status == "approaching_or_nearby":
        recommendation = "Keep Watchman open. Be ready for lightning, heavy rain, and quick changes."
    elif status == "possible":
        recommendation = "Monitor conditions. Storm timing may still change."
    else:
        recommendation = "No strong storm-arrival signal is detected from current Watchman inputs."

    return {
        "mode": "Watchman Storm Arrival Engine V1",
        "status": status,
        "arrivalEstimate": arrival,
        "arrivalMinutes": arrival_minutes,
        "confidence": confidence,
        "stormSignal": storm_signal,
        "threatScore": threat,
        "precipChance": precip,
        "recommendation": recommendation,
        "answer": (
            f"Storm Arrival Engine V1: {status}. "
            f"Estimated arrival: {arrival}. "
            f"Confidence: {confidence}%. {recommendation}"
        ),
        "note": "V1 estimates arrival from Watchman storm signal, alerts, precipitation, and hourly forecast timing. Live radar motion vectors are next phase.",
    }
