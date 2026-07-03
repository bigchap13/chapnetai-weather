def explain_reasoning_intelligence(question, weather):
    weather = weather or {}
    q = str(question or "").lower()

    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    observation = weather.get("observation") or {}

    first = forecast[0] if forecast and isinstance(forecast[0], dict) else {}
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}
    changed = watchman.get("whatChanged") or {}

    evidence = []

    if observation:
        evidence.append("live observation data is available")

    if first:
        evidence.append(f"nearest forecast period is {first.get('name', 'current period')} with {first.get('shortForecast', 'conditions updating')}")

    if alerts:
        evidence.append(f"{len(alerts)} active NWS alert(s) are present")

    if storm:
        evidence.append(f"storm tracker reports {storm.get('nearestStorm', 'unknown')} with {storm.get('intensity', 'unknown')} intensity")

    if intel:
        evidence.append(
            f"storm={intel.get('stormSignal', 'unknown')}, heat={intel.get('heatSignal', 'unknown')}, flood={intel.get('floodSignal', 'unknown')}"
        )

    if changed.get("changes"):
        evidence.append("change detector has recent scan comparison data")

    if hourly:
        evidence.append(f"{min(len(hourly), 24)} hourly forecast period(s) are loaded")

    confidence = 60
    confidence += 10 if observation else 0
    confidence += 10 if forecast else 0
    confidence += 10 if hourly else 0
    confidence += 8 if alerts else 0
    confidence += 8 if storm else 0
    confidence = min(confidence, 96)

    if "why" in q or "reason" in q or "evidence" in q or "explain" in q:
        answer = "Watchman based the recommendation on: " + "; ".join(evidence or ["available forecast context"])
    else:
        answer = "Watchman reasoning engine is active and ready to explain any recommendation."

    return {
        "mode": "Watchman Explain Reasoning Intelligence",
        "answer": answer,
        "confidence": confidence,
        "evidence": evidence or ["forecast context available"],
        "whatWouldChangeTheAnswer": [
            "new NWS alert",
            "forecast update",
            "storm tracker change",
            "radar trend change",
            "hourly timing shift",
        ],
    }
