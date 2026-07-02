from watchman_core.weather_operations_center import analyze_weather as _watchman_analyze_weather


def analyze_weather(alerts=None, forecast=None, observation=None, location=None):
    payload = {
        "alerts": alerts or [],
        "forecast": forecast or [],
        "observation": observation or {},
        "location": location or "",
    }

    result = _watchman_analyze_weather(payload)
    intel = result.get("weather_intelligence", {})
    risk = intel.get("risk", {})

    score = int(risk.get("score", 0) or 0)
    level = str(risk.get("risk_level", "normal") or "normal")
    hazards = risk.get("hazards", []) or []

    return {
        "engine": "Watchman",
        "version": "V108",
        "watchman_version": "Watchman V108",
        "coreAvailable": True,
        "coreModules": [
            "weather_risk_model",
            "weather_alerts",
            "weather_briefings",
            "weather_operations_center",
        ],
        "threatLevel": level,
        "threatScore": min(score, 100),
        "briefing": intel.get("briefing") or risk.get("summary") or "Watchman V108 weather briefing complete.",
        "outdoorIndex": max(0, 100 - min(score, 100)),
        "travelIndex": max(0, 100 - min(score, 100)),
        "reasons": hazards if hazards else ["Watchman V108 scan complete"],
        "raw": result,
    }


def run_watchman_weather(payload=None):
    return _watchman_analyze_weather(payload or {})
