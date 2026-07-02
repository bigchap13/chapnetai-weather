from datetime import datetime, timezone

WATCHMAN_VERSION = "V107"
WATCHMAN_SOURCE = "real ~/watchman core import"

CORE_MODULES = []

def try_import(name):
    try:
        __import__(f"watchman_core.{name}")
        CORE_MODULES.append(name)
        return True
    except Exception:
        return False

for module in [
    "ai_registry",
    "ai_health",
    "ai_oversight",
    "ai_briefings",
    "approval_queue",
    "executive_brief",
    "executive_dashboard",
    "intervention_queue",
    "workforce_risk_model",
    "workforce_intelligence",
]:
    try_import(module)

def severity_score(alert):
    severity = alert.get("severity")
    urgency = alert.get("urgency")
    certainty = alert.get("certainty")
    event = (alert.get("event") or "").lower()

    score = {
        "Extreme": 90,
        "Severe": 72,
        "Moderate": 48,
        "Minor": 25,
        "Unknown": 12,
    }.get(severity or "Unknown", 12)

    score += {
        "Immediate": 14,
        "Expected": 9,
        "Future": 5,
        "Past": 0,
        "Unknown": 2,
    }.get(urgency or "Unknown", 2)

    score += {
        "Observed": 10,
        "Likely": 8,
        "Possible": 4,
        "Unlikely": 1,
        "Unknown": 2,
    }.get(certainty or "Unknown", 2)

    if "tornado warning" in event:
        score += 25
    elif "flash flood warning" in event:
        score += 22
    elif "severe thunderstorm warning" in event:
        score += 18
    elif "excessive heat warning" in event:
        score += 16
    elif "heat advisory" in event:
        score += 10
    elif "watch" in event:
        score += 8
    elif "advisory" in event:
        score += 5

    return min(100, score)

def level(score):
    if score >= 85:
        return "EXTREME"
    if score >= 65:
        return "HIGH"
    if score >= 35:
        return "ELEVATED"
    return "LOW"

def analyze_weather(alerts, forecast_periods, observation, location="selected location"):
    scores = []
    reasons = []

    for alert in alerts or []:
        scores.append(severity_score(alert))
        if alert.get("event"):
            reasons.append(alert["event"])

    forecast_text = " ".join(
        f"{p.get('shortForecast','')} {p.get('detailedForecast','')}"
        for p in (forecast_periods or [])[:4]
    ).lower()

    language_checks = [
        (70, "tornado", "tornado forecast language"),
        (62, "flash flood", "flash flood forecast language"),
        (58, "severe thunderstorm", "severe storm forecast language"),
        (52, "heavy rain", "heavy rain forecast language"),
        (45, "heat index", "heat index language"),
        (40, "thunderstorm", "storm potential"),
    ]

    for pts, phrase, reason in language_checks:
        if phrase in forecast_text:
            scores.append(pts)
            reasons.append(reason)

    if observation:
        temp = observation.get("temperatureF")
        dew = observation.get("dewpointF")
        wind = observation.get("windMph") or 0
        gust = observation.get("gustMph") or 0
        max_wind = max(wind, gust)

        if temp is not None and temp >= 95:
            scores.append(42)
            reasons.append("high observed temperature")

        if temp is not None and dew is not None and temp >= 90 and dew >= 70:
            scores.append(52)
            reasons.append("dangerous heat and humidity combination")

        if max_wind >= 40:
            scores.append(60)
            reasons.append("high wind observation")
        elif max_wind >= 25:
            scores.append(35)
            reasons.append("elevated wind observation")

    score = max(scores) if scores else 0
    threat = level(score)

    if not reasons:
        reasons = ["No major immediate hazard detected from available NWS data"]

    events = sorted(set([a.get("event") for a in alerts or [] if a.get("event")]))

    if events:
        briefing = f"Watchman {WATCHMAN_VERSION} briefing: {threat} weather risk for {location}. Active NWS products include {', '.join(events[:5])}. Follow official National Weather Service guidance."
    else:
        first = forecast_periods[0] if forecast_periods else {}
        briefing = f"Watchman {WATCHMAN_VERSION} briefing: {threat} weather risk for {location}. Current NWS forecast: {first.get('shortForecast', 'No summary available')}."

    return {
        "engine": "Watchman Weather Intelligence",
        "version": WATCHMAN_VERSION,
        "source": WATCHMAN_SOURCE,
        "coreAvailable": len(CORE_MODULES) > 0,
        "coreModules": CORE_MODULES,
        "threatLevel": threat,
        "threatScore": score,
        "reasons": list(dict.fromkeys(reasons))[:8],
        "activeAlertEvents": events,
        "outdoorIndex": max(0, 100 - score),
        "travelIndex": max(0, 100 - score - (10 if score >= 50 else 0)),
        "briefing": briefing,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
