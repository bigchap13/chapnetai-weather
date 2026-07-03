def confidence_v2(weather, reasoning=None, module_result=None):
    weather = weather or {}
    alerts = weather.get("alerts") or []
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    obs = weather.get("observation") or {}
    watchman = weather.get("watchman") or {}
    storm = watchman.get("stormTracker") or {}

    scores = {
        "observationConfidence": 90 if obs else 45,
        "forecastConfidence": 88 if forecast else 45,
        "hourlyConfidence": 86 if hourly else 40,
        "alertConfidence": 95 if alerts else 75,
        "stormSignalConfidence": 85 if storm else 55,
        "reasoningConfidence": 90 if reasoning else 60,
        "moduleConfidence": 90 if module_result else 60,
    }

    overall = min(96, int(sum(scores.values()) / len(scores)))

    reasons = []
    if obs:
        reasons.append("live observation data is available")
    if forecast:
        reasons.append("forecast periods are loaded")
    if hourly:
        reasons.append("hourly timing is available")
    if alerts:
        reasons.append(f"{len(alerts)} official alert(s) are active")
    if storm:
        reasons.append("storm tracker context is available")
    if reasoning:
        reasons.append("reasoning tree was evaluated")
    if module_result:
        reasons.append("specialist module result was included")

    return {
        "mode": "Watchman Confidence V2",
        "overallConfidence": overall,
        "scores": scores,
        "reasons": reasons or ["limited available evidence"],
        "answer": (
            f"Watchman Confidence V2: overall confidence is {overall}%. "
            f"Reason: {'; '.join(reasons or ['limited available evidence'])}."
        ),
        "whatWouldImproveConfidence": [
            "newer observation data",
            "updated hourly forecast",
            "radar trend data",
            "more precise alert location",
            "specialist module agreement",
        ],
    }
