def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def explain_watchman_decision(weather, mission_result=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []

    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)
    outdoor = _safe_int(watchman.get("outdoorIndex"), 0)
    travel = _safe_int(watchman.get("travelIndex"), 0)

    factors = []

    if alerts:
        factors.append({
            "label": "Active NWS Alerts",
            "points": min(25, 10 + len(alerts) * 5),
            "reason": f"{len(alerts)} active alert(s) are affecting the decision.",
        })

    if threat:
        factors.append({
            "label": "Watchman Threat Score",
            "points": min(30, max(1, threat // 3)),
            "reason": f"Threat score is {threat}/100.",
        })

    if precip:
        factors.append({
            "label": "Rain Chance",
            "points": min(20, precip // 5),
            "reason": f"Precipitation chance is {precip}%.",
        })

    if outdoor:
        risk = max(0, 100 - outdoor)
        if risk:
            factors.append({
                "label": "Outdoor Risk",
                "points": min(20, risk // 4),
                "reason": f"Outdoor index is {outdoor}/100.",
            })

    if travel:
        risk = max(0, 100 - travel)
        if risk:
            factors.append({
                "label": "Travel Risk",
                "points": min(20, risk // 4),
                "reason": f"Travel index is {travel}/100.",
            })

    if mission_result:
        factors.append({
            "label": "Mission Context",
            "points": max(0, 100 - _safe_int(mission_result.get("score"), 100)) // 4,
            "reason": f"Mission verdict is {mission_result.get('verdict')}.",
        })

    total = sum(f["points"] for f in factors)
    total = max(0, min(100, total))

    if total >= 70:
        level = "high"
    elif total >= 40:
        level = "elevated"
    elif total >= 20:
        level = "guarded"
    else:
        level = "low"

    return {
        "mode": "Watchman Decision Explanation Engine V1",
        "riskLevel": level,
        "explanationScore": total,
        "factors": factors or [{
            "label": "No Major Signal",
            "points": 0,
            "reason": "No major risk factor was detected.",
        }],
        "whatWouldChange": [
            "Alerts expire or downgrade.",
            "Radar clears near the watched location.",
            "Rain and lightning signals decrease.",
            "Heat or wind risk drops.",
        ],
        "answer": f"Decision explanation: {level} risk, built from {len(factors)} factor(s).",
    }
