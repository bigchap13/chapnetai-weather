def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _text_blob(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []
    alerts = weather.get("alerts") or []
    watchman = weather.get("watchman") or {}

    parts = []

    for a in alerts:
        if isinstance(a, dict):
            parts.extend([
                str(a.get("event", "")),
                str(a.get("headline", "")),
                str(a.get("description", "")),
            ])

    for f in forecast[:6]:
        if isinstance(f, dict):
            parts.extend([
                str(f.get("shortForecast", "")),
                str(f.get("detailedForecast", "")),
            ])

    for h in hourly[:12]:
        if isinstance(h, dict):
            parts.append(str(h.get("shortForecast", "")))

    parts.extend([
        str(watchman.get("aiBriefing", "")),
        str(watchman.get("aiWeatherNarrative", "")),
    ])

    return " ".join(parts).lower()


def _detect_decision_type(question):
    q = str(question or "").lower()

    buckets = {
        "travel": ["drive", "leave", "trip", "commute", "road", "travel"],
        "outdoor": ["mow", "yard", "outside", "grill", "hike", "walk", "camp", "golf"],
        "construction": ["concrete", "roof", "paint", "pressure wash", "excavate", "crane", "construction"],
        "sports": ["practice", "game", "baseball", "football", "soccer", "run", "cycling"],
        "pets": ["dog", "pet", "cat", "livestock", "horse", "cattle"],
        "home": ["windows", "sprinkler", "generator", "power", "pipes", "hvac", "solar"],
        "event": ["wedding", "party", "festival", "cookout", "concert", "fireworks"],
        "emergency": ["emergency", "shelter", "evacuate", "danger", "worst", "biggest threat"],
    }

    for name, words in buckets.items():
        if any(w in q for w in words):
            return name

    return "general"


def decision_intelligence(question, weather):
    weather = weather or {}
    q = str(question or "").lower()
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    hourly = weather.get("hourly") or []
    storm = watchman.get("stormTracker") or {}
    intel = watchman.get("liveStormIntelligence") or {}

    decision_type = _detect_decision_type(question)

    outdoor = _safe_int(watchman.get("outdoorIndex"), 50)
    travel = _safe_int(watchman.get("travelIndex"), 50)
    threat_score = _safe_int(watchman.get("threatScore"), 0)
    text = _text_blob(weather)

    storm_active = (
        storm.get("nearestStorm") == "Detected"
        or intel.get("stormSignal") == "detected"
        or "thunderstorm" in text
        or "lightning" in text
    )
    heat_active = intel.get("heatSignal") == "detected" or "heat advisory" in text or "heat index" in text
    flood_active = intel.get("floodSignal") == "detected" or "flood" in text
    wind_active = any(w in text for w in ["damaging wind", "wind advisory", "high wind"])
    winter_active = any(w in text for w in ["snow", "ice", "sleet", "freezing rain", "black ice"])
    alert_active = len(alerts) > 0

    if decision_type == "travel":
        score = travel
    elif decision_type in ["construction", "sports", "pets", "event", "outdoor"]:
        score = outdoor
    elif decision_type == "emergency":
        score = 100 - threat_score
    else:
        score = min(outdoor, travel)

    evidence = []
    do_now = []
    avoid = []
    change = []

    if alert_active:
        score -= 10
        evidence.append(f"{len(alerts)} active NWS alert(s)")
        change.append("active alerts expire or change")

    if storm_active:
        score -= 30
        evidence.append("storm or lightning signal is active")
        do_now.append("keep radar and alerts open")
        avoid.append("avoid exposed outdoor activity")
        change.append("storm tracker clears or radar shows storms moving away")

    if heat_active:
        score -= 20
        evidence.append("heat signal is active")
        do_now.append("hydrate and use shade or cooling breaks")
        avoid.append("avoid peak heat if possible")
        change.append("heat index drops")

    if flood_active:
        score -= 25
        evidence.append("flood signal is active")
        do_now.append("avoid low-water crossings")
        avoid.append("never drive through water-covered roads")
        change.append("flood signal clears")

    if wind_active:
        score -= 15
        evidence.append("wind impact signal is active")
        avoid.append("avoid loose objects, cranes, ladders, and exposed water")
        change.append("wind decreases")

    if winter_active:
        score -= 30
        evidence.append("winter road signal is active")
        avoid.append("watch bridges, overpasses, and shaded roads")
        change.append("temperatures rise and winter precipitation clears")

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "YES"
        recommendation = "Conditions look usable. Recheck Watchman before starting."
        best_time = "current window"
    elif score >= 45:
        verdict = "CAUTION"
        recommendation = "Proceed only with monitoring and a backup plan."
        best_time = "short monitored window"
    else:
        verdict = "NO"
        recommendation = "Delay if possible until hazard signals improve."
        best_time = "wait for a lower-risk window"

    if not evidence:
        evidence.append("no major Watchman hazard signal is active")
    if not do_now:
        do_now.append("recheck Watchman before starting")
    if not avoid:
        avoid.append("avoid ignoring sudden weather changes")
    if not change:
        change.append("new alerts, radar changes, or forecast changes")

    worst_time = "during storms, warnings, peak heat, flooding, strong wind, or low visibility"

    return {
        "mode": "Watchman Decision Intelligence",
        "decisionType": decision_type,
        "verdict": verdict,
        "score": score,
        "confidence": 88,
        "recommendation": recommendation,
        "bestTime": best_time,
        "worstTime": worst_time,
        "evidence": evidence,
        "doNow": do_now,
        "avoid": avoid,
        "whatWouldChangeTheAnswer": change,
        "answer": (
            f"{verdict}: {recommendation} Decision score: {score}/100. "
            f"Best time: {best_time}. Worst time: {worst_time}. "
            f"Evidence: {'; '.join(evidence)}. "
            f"What would change the answer: {'; '.join(change)}."
        ),
    }
