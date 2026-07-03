def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _text(weather):
    weather = weather or {}
    parts = []

    for key in ["alerts", "forecast", "hourly"]:
        for item in weather.get(key, []) or []:
            if isinstance(item, dict):
                parts.extend(str(v) for v in item.values() if isinstance(v, (str, int, float)))

    watchman = weather.get("watchman") or {}
    parts.extend(str(v) for v in watchman.values() if isinstance(v, (str, int, float)))

    return " ".join(parts).lower()


def reasoning_engine_v2(question, weather, module_result=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    obs = weather.get("observation") or {}
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}
    blob = _text(weather)

    evidence = []
    conflicts = []
    score = 80

    if alerts:
        score -= 35
        evidence.append({"source": "official_alerts", "impact": -35, "detail": f"{len(alerts)} active alert(s)"})

    if storm.get("nearestStorm") == "Detected" or intel.get("stormSignal") == "detected" or "thunderstorm" in blob:
        score -= 30
        evidence.append({"source": "storm_lightning", "impact": -30, "detail": "storm or lightning signal detected"})

    if intel.get("heatSignal") == "detected" or "heat advisory" in blob or "heat index" in blob:
        score -= 20
        evidence.append({"source": "heat", "impact": -20, "detail": "heat signal detected"})

    if intel.get("floodSignal") == "detected" or "flood" in blob:
        score -= 25
        evidence.append({"source": "flood", "impact": -25, "detail": "flood signal detected"})

    if "mostly clear" in blob or "clear" in blob:
        score += 10
        evidence.append({"source": "sky_condition", "impact": 10, "detail": "clear-sky wording supports lower weather friction"})

    if "clear" in blob and ("storm" in blob or "thunderstorm" in blob):
        conflicts.append("Current condition appears calm, but forecast or storm language still shows storm potential.")

    if module_result and isinstance(module_result, dict):
        combined = _safe_int(module_result.get("combinedScore"), 50)
        if combined < 45:
            score -= 15
            evidence.append({"source": "multi_module", "impact": -15, "detail": "multi-module reasoning is unfavorable"})
        elif combined >= 75:
            score += 10
            evidence.append({"source": "multi_module", "impact": 10, "detail": "multi-module reasoning is favorable"})

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "YES"
        recommendation = "Conditions look usable with normal Watchman monitoring."
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Conditions are mixed. Use monitoring, timing, and a backup plan."
    else:
        verdict = "NO"
        recommendation = "Delay if possible until the main risk signals improve."

    primary = sorted(evidence, key=lambda x: abs(x["impact"]), reverse=True)[:3]

    return {
        "mode": "Watchman Reasoning Engine V2",
        "verdict": verdict,
        "score": score,
        "confidence": 90 if evidence else 70,
        "recommendation": recommendation,
        "primaryDrivers": primary,
        "conflicts": conflicts or ["no major contradiction detected"],
        "answer": (
            f"{verdict}: {recommendation} Reasoning Engine V2 score: {score}/100. "
            f"Primary drivers: {'; '.join(x['detail'] for x in primary) if primary else 'limited evidence'}. "
            f"Conflicts: {'; '.join(conflicts) if conflicts else 'none detected'}."
        ),
    }
