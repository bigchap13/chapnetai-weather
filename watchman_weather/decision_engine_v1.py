from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


def _alert_text(alerts):
    return " ".join(
        (str(a.get("event") or "") + " " + str(a.get("headline") or "")).lower()
        for a in alerts
        if isinstance(a, dict)
    )


def watchman_decision_engine(place, weather, impact=None, lightning=None, multi_cell=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []

    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)
    alert_count = len(alerts)

    impact = impact or {}
    lightning = lightning or {}
    multi_cell = multi_cell or {}

    impact_level = str(impact.get("highestImpact") or "unknown").lower()
    lightning_risk = str(lightning.get("risk") or "unknown").lower()
    tracked_cells = _safe_int(multi_cell.get("trackedCount"), 0)

    text = _alert_text(alerts)

    reasons = []
    recommendations = []
    score = threat

    if alert_count:
        score += 15
        reasons.append(f"{alert_count} active alert(s)")

    if "tornado warning" in text:
        score = max(score, 95)
        reasons.append("tornado warning detected")
        recommendations += [
            "Shelter immediately.",
            "Move to the lowest interior room.",
            "Stay away from windows.",
        ]

    elif "severe thunderstorm warning" in text:
        score = max(score, 80)
        reasons.append("severe thunderstorm warning detected")
        recommendations += [
            "Move indoors now.",
            "Stay away from windows.",
            "Delay travel until the warning passes.",
        ]

    elif "flash flood warning" in text:
        score = max(score, 82)
        reasons.append("flash flood warning detected")
        recommendations += [
            "Avoid flooded roads.",
            "Do not cross water-covered roadways.",
            "Move away from low-lying areas.",
        ]

    if impact_level == "high":
        score = max(score, 85)
        reasons.append("high projected impact")
        recommendations.append("Prepare for impact within the forecast window.")
    elif impact_level == "elevated":
        score = max(score, 70)
        reasons.append("elevated projected impact")
        recommendations.append("Prepare for quick weather changes.")
    elif impact_level == "possible":
        score = max(score, 55)
        reasons.append("possible projected impact")
        recommendations.append("Keep monitoring Watchman.")

    if lightning_risk == "high":
        score = max(score, 78)
        reasons.append("high lightning risk")
        recommendations.append("Stop outdoor activity and move inside.")
    elif lightning_risk == "elevated":
        score = max(score, 62)
        reasons.append("elevated lightning risk")
        recommendations.append("Stay close to shelter.")

    if tracked_cells:
        score += min(10, tracked_cells * 3)
        reasons.append(f"{tracked_cells} tracked storm cell(s)")

    if precip >= 50:
        score += 8
        reasons.append(f"precipitation chance {precip}%")

    score = min(score, 100)

    if score >= 90:
        severity = "extreme"
        decision = "Shelter Immediately"
    elif score >= 75:
        severity = "high"
        decision = "Move Indoors Now"
    elif score >= 55:
        severity = "elevated"
        decision = "Stay Weather-Aware"
    elif score >= 30:
        severity = "guarded"
        decision = "Monitor Conditions"
    else:
        severity = "low"
        decision = "No Immediate Action Needed"

    if not recommendations:
        if severity in ["low", "guarded"]:
            recommendations.append("Continue normal activity but keep Watchman available.")
        else:
            recommendations.append("Monitor radar, alerts, and updated Watchman scans.")

    # Deduplicate while preserving order.
    deduped = []
    for r in recommendations:
        if r not in deduped:
            deduped.append(r)

    return {
        "mode": "Watchman Decision Engine V1",
        "time": _now(),
        "place": place,
        "decision": decision,
        "severity": severity,
        "decisionScore": score,
        "confidence": min(95, 55 + len(reasons) * 8),
        "primaryThreat": (
            "Tornado" if "tornado warning" in text else
            "Severe Thunderstorm" if "severe thunderstorm warning" in text else
            "Flash Flooding" if "flash flood warning" in text else
            "Lightning" if lightning_risk in ["high", "elevated"] else
            "Storm Impact" if impact_level in ["high", "elevated", "possible"] else
            "General Weather"
        ),
        "inputs": {
            "alerts": alert_count,
            "threatScore": threat,
            "precipChance": precip,
            "impactLevel": impact_level,
            "lightningRisk": lightning_risk,
            "trackedCells": tracked_cells,
        },
        "reasons": reasons or ["No major threat signal detected."],
        "recommendations": deduped,
        "answer": f"Decision Engine V1: {decision}. Severity: {severity}. Score: {score}/100.",
    }
