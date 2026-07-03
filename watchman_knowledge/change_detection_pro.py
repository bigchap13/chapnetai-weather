def change_detection_pro(weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    changed = watchman.get("whatChanged") or {}

    changes = changed.get("changes") or []
    status = changed.get("status") or "unknown"
    summary = changed.get("summary") or "No previous scan comparison is available yet."

    worsening_words = ["increased", "worsened", "warning", "storm", "higher"]
    improving_words = ["decreased", "improved", "cleared", "lower"]

    text = " ".join(changes).lower()

    if any(w in text for w in worsening_words):
        trend = "worsening"
        recommendation = "Increase weather awareness and keep Watchman open."
    elif any(w in text for w in improving_words):
        trend = "improving"
        recommendation = "Conditions may be improving, but continue monitoring."
    else:
        trend = "steady"
        recommendation = "No major change detected. Continue normal monitoring."

    return {
        "mode": "Watchman Change Detection Pro",
        "status": status,
        "trend": trend,
        "summary": summary,
        "changes": changes or ["No major Watchman changes since the previous scan."],
        "recommendation": recommendation,
        "confidence": 84,
        "whatWouldChangeTheAnswer": [
            "threat score changes",
            "active alert count changes",
            "precipitation chance changes",
            "storm signal changes",
            "nearest forecast wording changes",
        ],
    }
