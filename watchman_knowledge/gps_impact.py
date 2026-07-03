from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def gps_impact_forecast(label, lat, lon, weather, multi_cell=None, impact=None, decision=None):
    impact = impact or {}
    decision = decision or {}
    multi_cell = multi_cell or {}

    return {
        "mode": "Watchman GPS-Aware Impact Forecast V1",
        "time": _now(),
        "label": label,
        "gps": {
            "lat": lat,
            "lon": lon,
        },
        "impact": {
            "highestImpact": impact.get("highestImpact"),
            "trackedCells": impact.get("trackedCells"),
            "impactCount": impact.get("impactCount"),
            "featureCount": impact.get("featureCount"),
            "impacts": impact.get("impacts") or [],
            "features": impact.get("features") or [],
        },
        "decision": {
            "decision": decision.get("decision"),
            "severity": decision.get("severity"),
            "score": decision.get("decisionScore"),
            "confidence": decision.get("confidence"),
            "primaryThreat": decision.get("primaryThreat"),
            "recommendations": decision.get("recommendations") or [],
            "reasons": decision.get("reasons") or [],
        },
        "multiCell": {
            "cellCount": multi_cell.get("cellCount"),
            "trackedCount": multi_cell.get("trackedCount"),
            "tracks": multi_cell.get("tracks") or [],
        },
        "answer": (
            f"GPS Impact Forecast V1 for {label}: "
            f"{decision.get('decision', 'No decision available')}. "
            f"Impact: {impact.get('highestImpact', 'unknown')}."
        ),
        "note": "This uses the supplied GPS coordinates as the forecast center. It is not hardcoded to Walker County or any fixed place.",
    }
