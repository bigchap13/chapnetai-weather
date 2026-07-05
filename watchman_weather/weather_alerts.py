WATCHMAN_WEATHER_VERSION = "Watchman V108"


def extract_alerts(payload=None):
    payload = payload or {}
    raw = payload.get("alerts") or payload.get("features") or []

    if isinstance(raw, dict):
        raw = raw.get("features") or raw.get("alerts") or []

    if not isinstance(raw, list):
        return []

    alerts = []

    for item in raw:
        if not isinstance(item, dict):
            continue

        props = item.get("properties") if isinstance(item.get("properties"), dict) else item

        alerts.append({
            "event": str(props.get("event") or props.get("headline") or "Weather Alert"),
            "severity": str(props.get("severity") or props.get("urgency") or "unknown"),
            "headline": str(props.get("headline") or props.get("event") or "Weather Alert"),
            "description": str(props.get("description") or ""),
            "instruction": str(props.get("instruction") or ""),
            "area": str(props.get("areaDesc") or props.get("area") or ""),
        })

    return alerts


def summarize_alerts(payload=None):
    alerts = extract_alerts(payload)
    severe = 0

    for alert in alerts:
        text = " ".join(str(v).lower() for v in alert.values())
        if "warning" in text or "severe" in text or "emergency" in text:
            severe += 1

    return {
        "watchman_version": WATCHMAN_WEATHER_VERSION,
        "active_alert_count": len(alerts),
        "severe_alert_count": severe,
        "active_alerts": alerts,
    }
