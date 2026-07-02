from watchman_core.weather_operations_center import analyze_weather as _watchman_analyze_weather


def _watchman_ai_features(alerts=None, forecast=None, observation=None, location=None, score=0, level="normal"):
    alerts = alerts or []
    forecast = forecast or []
    location = location or "this location"

    text = " ".join([
        str(location),
        " ".join(str(a.get("event", "")) + " " + str(a.get("headline", "")) for a in alerts if isinstance(a, dict)),
        " ".join(str(f.get("shortForecast", "")) + " " + str(f.get("detailedForecast", "")) for f in forecast[:4] if isinstance(f, dict)),
    ]).lower()

    storm_words = ["thunderstorm", "showers", "lightning", "severe"]
    heat_words = ["heat advisory", "heat index", "hot", "extreme heat"]
    flood_words = ["flood", "heavy rain", "flash flood"]

    storm_risk = any(w in text for w in storm_words)
    heat_risk = any(w in text for w in heat_words)
    flood_risk = any(w in text for w in flood_words)

    next_period = forecast[0] if forecast and isinstance(forecast[0], dict) else {}
    next_name = next_period.get("name") or "the next forecast period"
    next_short = next_period.get("shortForecast") or "conditions updating"
    next_temp = next_period.get("temperature")
    pop = ((next_period.get("probabilityOfPrecipitation") or {}).get("value"))

    if storm_risk:
        ai_brief = f"Watchman sees storm potential near {location}. Expect {next_short.lower()} during {next_name}. Keep radar open and be ready for lightning or heavy rain."
    elif heat_risk:
        ai_brief = f"Watchman sees heat risk near {location}. Limit strenuous outdoor work, hydrate often, and use shade or air conditioning during peak heat."
    elif flood_risk:
        ai_brief = f"Watchman sees flooding indicators near {location}. Watch low-water crossings, poor-drainage roads, and rapidly changing rainfall rates."
    else:
        ai_brief = f"Watchman sees no immediate severe-weather signal near {location}. Continue normal awareness and monitor updates."

    if pop is None:
        eta = "No precise precipitation arrival signal available yet."
    elif pop >= 60:
        eta = "Rain or storms may arrive during the current forecast window. Keep radar active now."
    elif pop >= 30:
        eta = "Rain or storms are possible within the next few hours. Watchman recommends checking radar before outdoor activity."
    elif pop > 0:
        eta = "Low precipitation chance, but isolated development remains possible."
    else:
        eta = "No near-term rain arrival signal from the current forecast period."

    storm_intel = {
        "status": "active scan",
        "stormSignal": "detected" if storm_risk else "not detected",
        "heatSignal": "detected" if heat_risk else "not detected",
        "floodSignal": "detected" if flood_risk else "not detected",
        "nextWindow": next_name,
        "nextConditions": next_short,
        "precipChance": pop,
        "temperature": next_temp,
        "watchmanAssessment": level,
    }

    arrival = {
        "rainEta": eta,
        "lightningEta": "Lightning risk increases if nearby thunderstorms develop." if storm_risk else "No lightning arrival signal detected.",
        "streetLevelNote": "Street-level timing is estimated from NWS forecast periods and local radar context.",
    }

    return {
        "aiBriefing": ai_brief,
        "liveStormIntelligence": storm_intel,
        "streetLevelArrival": arrival,
    }


_LAST_WEATHER_STATE = {}


def _compare_weather_state(location, score, level, alerts, forecast, storm_intel):
    key = str(location or "default").lower()
    alerts = alerts or []
    forecast = forecast or []

    current = {
        "score": int(score or 0),
        "level": str(level or "normal"),
        "alert_count": len(alerts),
        "first_forecast": (forecast[0].get("shortForecast") if forecast and isinstance(forecast[0], dict) else ""),
        "precip": ((forecast[0].get("probabilityOfPrecipitation") or {}).get("value") if forecast and isinstance(forecast[0], dict) else None),
        "storm": storm_intel.get("stormSignal"),
        "heat": storm_intel.get("heatSignal"),
        "flood": storm_intel.get("floodSignal"),
    }

    previous = _LAST_WEATHER_STATE.get(key)
    _LAST_WEATHER_STATE[key] = current

    if not previous:
        return {
            "status": "first_scan",
            "summary": "First Watchman scan for this location. Future scans will show what changed.",
            "changes": ["Baseline established for this location."],
        }

    changes = []

    if current["alert_count"] > previous["alert_count"]:
        changes.append(f"Active alerts increased from {previous['alert_count']} to {current['alert_count']}.")
    elif current["alert_count"] < previous["alert_count"]:
        changes.append(f"Active alerts decreased from {previous['alert_count']} to {current['alert_count']}.")

    if current["score"] > previous["score"]:
        changes.append(f"Threat score worsened by {current['score'] - previous['score']} points.")
    elif current["score"] < previous["score"]:
        changes.append(f"Threat score improved by {previous['score'] - current['score']} points.")

    if current["level"] != previous["level"]:
        changes.append(f"Threat level changed from {previous['level']} to {current['level']}.")

    if current["precip"] != previous["precip"]:
        changes.append(f"Precipitation chance changed from {previous['precip']}% to {current['precip']}%.")

    for label in ["storm", "heat", "flood"]:
        if current[label] != previous[label]:
            changes.append(f"{label.title()} signal changed from {previous[label]} to {current[label]}.")

    if current["first_forecast"] != previous["first_forecast"]:
        changes.append("Nearest forecast wording changed.")

    if not changes:
        changes.append("No major Watchman changes since the previous scan.")

    return {
        "status": "updated",
        "summary": "Watchman compared this scan against the previous scan for the same location.",
        "changes": changes,
    }


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

    ai = _watchman_ai_features(alerts, forecast, observation, location, score, level)
    changed = _compare_weather_state(location, score, level, alerts, forecast, ai["liveStormIntelligence"])

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
        "aiBriefing": ai["aiBriefing"],
        "liveStormIntelligence": ai["liveStormIntelligence"],
        "streetLevelArrival": ai["streetLevelArrival"],
        "whatChanged": changed,
        "raw": result,
    }


def run_watchman_weather(payload=None):
    return _watchman_analyze_weather(payload or {})
