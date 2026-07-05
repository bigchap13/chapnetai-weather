from __future__ import annotations

from typing import Any, Dict, Tuple


def _safe(v: Any, default: str = "") -> str:
    if v is None:
        return default
    return str(v).strip()


def build_smart_notification_text(notification: Dict[str, Any]) -> Tuple[str, str]:
    """
    Converts raw Watchman notifications into sharper phone-alert language.

    Returns:
      (title, body)
    """
    kind = _safe(notification.get("kind")).lower()
    place = _safe(notification.get("place"), "your location")
    title = _safe(notification.get("title"), "Watchman Weather Alert")
    message = _safe(notification.get("message"))

    data = notification.get("data") or {}

    if kind == "radar":
        radar = data.get("radar") or {}
        verdict = _safe(radar.get("verdict"))
        score = radar.get("score")
        arrival = _safe(radar.get("arrivalEstimate"))
        recommendation = _safe(radar.get("recommendation"))

        parts = []

        if verdict:
            if score not in (None, ""):
                parts.append(f"Storm risk is {verdict} near {place} ({score}/100).")
            else:
                parts.append(f"Storm risk is {verdict} near {place}.")
        else:
            parts.append(f"Storm risk is elevated near {place}.")

        if arrival:
            parts.append(f"Arrival estimate: {arrival}.")

        if recommendation:
            parts.append(recommendation)

        return "Watchman storm risk", " ".join(parts).strip()

    if kind == "alert":
        alert_count = data.get("alertCount")
        threat_score = data.get("threatScore")

        parts = []

        if alert_count:
            parts.append(f"{alert_count} active weather alert(s) near {place}.")
        else:
            parts.append(f"Active weather alert near {place}.")

        if threat_score not in (None, ""):
            parts.append(f"Threat score: {threat_score}.")

        if message:
            parts.append(message)

        return "Watchman weather alert", " ".join(parts).strip()

    if kind in ("lightning", "storm", "arrival"):
        arrival = _safe(data.get("arrivalEstimate") or data.get("arrival"))
        distance = _safe(data.get("distance") or data.get("distanceMiles"))
        direction = _safe(data.get("direction"))

        parts = [f"Weather risk changed near {place}."]

        if distance and direction:
            parts.append(f"Detected about {distance} miles {direction}.")
        if arrival:
            parts.append(f"Arrival estimate: {arrival}.")
        if message:
            parts.append(message)

        return "Watchman weather change", " ".join(parts).strip()

    return title, message or f"Weather risk changed near {place}."
