def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def reasoning_tree(question, weather, module_result=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    obs = weather.get("observation") or {}

    first = forecast[0] if forecast and isinstance(forecast[0], dict) else {}
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}

    branches = [
        {
            "branch": "official_alerts",
            "status": "active" if alerts else "clear",
            "weight": 30 if alerts else 5,
            "evidence": f"{len(alerts)} active alert(s)",
        },
        {
            "branch": "current_observation",
            "status": "available" if obs else "limited",
            "weight": 15 if obs else 5,
            "evidence": obs.get("text") or "observation unavailable",
        },
        {
            "branch": "forecast",
            "status": "available" if forecast else "limited",
            "weight": 20 if forecast else 5,
            "evidence": first.get("shortForecast") or "forecast unavailable",
        },
        {
            "branch": "hourly_timing",
            "status": "available" if hourly else "limited",
            "weight": 15 if hourly else 5,
            "evidence": f"{min(len(hourly), 24)} hourly period(s) loaded" if hourly else "hourly unavailable",
        },
        {
            "branch": "storm_signal",
            "status": storm.get("nearestStorm", "unknown"),
            "weight": 25 if storm.get("nearestStorm") == "Detected" else 5,
            "evidence": f"{storm.get('nearestStorm', 'unknown')} / {storm.get('intensity', 'unknown')}",
        },
        {
            "branch": "watchman_intelligence",
            "status": watchman.get("threatLevel", "unknown"),
            "weight": _safe_int(watchman.get("threatScore"), 0),
            "evidence": (
                f"threat={watchman.get('threatLevel', 'unknown')} "
                f"score={watchman.get('threatScore', 'unknown')} "
                f"storm={intel.get('stormSignal', 'unknown')} "
                f"heat={intel.get('heatSignal', 'unknown')} "
                f"flood={intel.get('floodSignal', 'unknown')}"
            ),
        },
    ]

    if isinstance(module_result, dict):
        branches.append({
            "branch": "specialist_module",
            "status": module_result.get("mode", "available"),
            "weight": _safe_int(module_result.get("combinedScore") or module_result.get("score"), 50),
            "evidence": module_result.get("recommendation") or module_result.get("answer") or "specialist module available",
        })

    threat_score = _safe_int(watchman.get("threatScore"), 0)

    if alerts or threat_score >= 60:
        conclusion = "high_attention"
        summary = "Official alerts or elevated Watchman threat scoring require close attention."
    elif threat_score >= 25 or storm.get("nearestStorm") == "Detected":
        conclusion = "monitor"
        summary = "Watchman sees signals that justify monitoring and backup planning."
    else:
        conclusion = "normal"
        summary = "No major Watchman escalation signal is active."

    return {
        "mode": "Watchman Reasoning Tree",
        "conclusion": conclusion,
        "summary": summary,
        "riskWeight": sum(b["weight"] for b in branches),
        "branches": branches,
        "answer": (
            f"Reasoning tree conclusion: {conclusion}. {summary} "
            f"Primary evidence: " + "; ".join(b["evidence"] for b in branches[:4])
        ),
    }
