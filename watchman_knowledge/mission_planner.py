def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


MISSIONS = {
    "mow": {
        "label": "Mow Grass",
        "good": ["low wind", "low rain chance", "lower heat"],
        "bad": ["lightning", "heat", "rain", "wet ground"],
    },
    "fish": {
        "label": "Fishing",
        "good": ["stable weather", "light wind"],
        "bad": ["lightning", "storms", "high wind"],
    },
    "motorcycle": {
        "label": "Motorcycle Ride",
        "good": ["dry roads", "good visibility"],
        "bad": ["rain", "fog", "strong wind", "lightning"],
    },
    "travel": {
        "label": "Travel",
        "good": ["clear visibility", "low storm risk"],
        "bad": ["heavy rain", "flooding", "fog", "warnings"],
    },
    "cookout": {
        "label": "Cookout",
        "good": ["dry window", "lower wind"],
        "bad": ["rain", "lightning", "heat"],
    },
    "walk": {
        "label": "Walking",
        "good": ["comfortable heat", "low lightning risk"],
        "bad": ["heat", "storms", "lightning"],
    },
    "roof": {
        "label": "Roof Work",
        "good": ["dry weather", "low wind"],
        "bad": ["heat", "lightning", "wind", "rain"],
    },
    "drone": {
        "label": "Drone Flight",
        "good": ["low wind", "dry weather"],
        "bad": ["wind", "rain", "storms"],
    },
}


def mission_planner(mission, weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    forecast = weather.get("forecast") or []

    mission_key = (mission or "travel").lower().strip()
    config = MISSIONS.get(mission_key, MISSIONS["travel"])

    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)
    outdoor = _safe_int(watchman.get("outdoorIndex"), 0)
    travel = _safe_int(watchman.get("travelIndex"), 0)

    text = " ".join([
        str(watchman.get("briefing") or ""),
        str(watchman.get("aiBriefing") or ""),
        str(watchman.get("aiWeatherNarrative") or ""),
        " ".join(str(a.get("event") or "") for a in alerts if isinstance(a, dict)),
        " ".join(str(f.get("shortForecast") or "") for f in forecast[:3] if isinstance(f, dict)),
    ]).lower()

    reasons = []
    score = 100

    if alerts:
        score -= 20
        reasons.append(f"{len(alerts)} active alert(s)")

    if threat >= 60:
        score -= 35
        reasons.append(f"threat score is high at {threat}/100")
    elif threat >= 35:
        score -= 20
        reasons.append(f"threat score is guarded at {threat}/100")
    elif threat >= 20:
        score -= 10
        reasons.append(f"threat score is elevated at {threat}/100")

    if precip >= 50:
        score -= 20
        reasons.append(f"rain chance is {precip}%")
    elif precip >= 30:
        score -= 10
        reasons.append(f"rain chance is {precip}%")

    if any(x in text for x in ["thunder", "lightning", "storm"]):
        score -= 18
        reasons.append("storm or lightning signal detected")

    if "heat" in text:
        score -= 12
        reasons.append("heat signal detected")

    if any(x in text for x in ["flood", "fog", "wind advisory", "strong wind"]):
        score -= 12
        reasons.append("visibility, flooding, or wind concern detected")

    score = max(0, min(100, score))

    if score >= 75:
        verdict = "GO"
        recommendation = "Conditions look acceptable for this mission."
    elif score >= 50:
        verdict = "CAUTION"
        recommendation = "This mission may be possible, but keep Watchman open and watch for changes."
    else:
        verdict = "WAIT"
        recommendation = "Delay this mission until weather signals improve."

    if mission_key in ["mow", "roof", "walk"] and ("heat" in text or precip >= 30):
        verdict = "WAIT" if score < 60 else "CAUTION"

    return {
        "mode": "Watchman Mission Planner V1",
        "mission": mission_key,
        "missionLabel": config["label"],
        "verdict": verdict,
        "score": score,
        "recommendation": recommendation,
        "reasons": reasons or ["No major hazard signal detected."],
        "goodFor": config["good"],
        "badFor": config["bad"],
        "answer": f"{config['label']}: {verdict}. {recommendation}",
    }


# Backward-compatible wrapper for existing app imports.
def build_mission_plan(mission, weather):
    return mission_planner(mission, weather)
