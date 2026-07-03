from datetime import datetime


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def _label_time(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%-I:%M %p")
    except Exception:
        return str(value or "Unknown")


def _hour_risk(hour):
    text = str(hour.get("shortForecast") or "").lower()
    temp = _safe_int(hour.get("temperature"), 0)
    pop = _safe_int((hour.get("probabilityOfPrecipitation") or {}).get("value"), 0)

    score = 0
    reasons = []

    if any(x in text for x in ["thunder", "storm"]):
        score += 35
        reasons.append("storm signal")

    if any(x in text for x in ["rain", "showers"]):
        score += 18
        reasons.append("rain signal")

    if pop >= 50:
        score += 20
        reasons.append(f"rain chance {pop}%")
    elif pop >= 30:
        score += 10
        reasons.append(f"rain chance {pop}%")

    if temp >= 95:
        score += 15
        reasons.append(f"heat {temp}°")
    elif temp >= 90:
        score += 8
        reasons.append(f"warm {temp}°")

    return max(0, min(100, score)), reasons


def build_live_timeline(place, weather):
    weather = weather or {}
    hourly = weather.get("hourly") or []
    alerts = weather.get("alerts") or []
    watchman = weather.get("watchman") or {}

    scored = []
    for h in hourly[:24]:
        if not isinstance(h, dict):
            continue
        risk, reasons = _hour_risk(h)
        scored.append({
            "time": _label_time(h.get("startTime")),
            "rawStartTime": h.get("startTime"),
            "risk": risk,
            "temperature": h.get("temperature"),
            "forecast": h.get("shortForecast"),
            "rainChance": _safe_int((h.get("probabilityOfPrecipitation") or {}).get("value"), 0),
            "wind": h.get("windSpeed"),
            "reasons": reasons or ["low signal"],
        })

    storm_hour = next((h for h in scored if h["risk"] >= 45), None)
    lightning_hour = next((h for h in scored if "storm signal" in h["reasons"]), None)
    safe_hour = next((h for h in scored if h["risk"] <= 20 and h["rainChance"] <= 25), None)

    events = []

    if alerts:
        events.append({
            "level": "alert",
            "title": "Active alert in effect",
            "time": "Now",
            "detail": f"{len(alerts)} active NWS alert(s).",
        })

    if lightning_hour:
        events.append({
            "level": "warning",
            "title": "Lightning risk increasing",
            "time": lightning_hour["time"],
            "detail": "Storm wording appears in the hourly forecast. Watchman recommends monitoring radar west and southwest of your location.",
        })

    if storm_hour:
        events.append({
            "level": "warning",
            "title": "Storm window begins",
            "time": storm_hour["time"],
            "detail": f"{storm_hour['forecast']} with {storm_hour['rainChance']}% rain chance.",
        })

    if safe_hour:
        events.append({
            "level": "safe",
            "title": "Safer window",
            "time": safe_hour["time"],
            "detail": f"Lower-risk window: {safe_hour['forecast']}, {safe_hour['rainChance']}% rain chance.",
        })

    if not events:
        events.append({
            "level": "safe",
            "title": "No major near-term hazard signal",
            "time": "Now",
            "detail": "Watchman does not see a strong storm, rain, heat, or alert signal in the near-term timeline.",
        })

    return {
        "mode": "Watchman Live Timeline",
        "place": place,
        "summary": events[0]["detail"],
        "events": events,
        "hours": scored[:12],
        "notificationReason": {
            "activeAlerts": len(alerts),
            "watchmanThreatLevel": watchman.get("threatLevel"),
            "watchmanThreatScore": watchman.get("threatScore"),
            "stormWindowFound": bool(storm_hour),
            "lightningWindowFound": bool(lightning_hour),
            "safeWindowFound": bool(safe_hour),
        },
    }
