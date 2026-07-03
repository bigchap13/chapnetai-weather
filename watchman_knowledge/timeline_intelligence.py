def _hour_text(hour):
    if not isinstance(hour, dict):
        return ""
    return " ".join(str(hour.get(k, "")) for k in ["shortForecast", "temperature", "windSpeed"]).lower()


def _window_score(text, base=80):
    score = base
    risks = []

    if "thunderstorm" in text or "storm" in text:
        score -= 35
        risks.append("storm risk")
    if "rain" in text or "showers" in text:
        score -= 20
        risks.append("rain risk")
    if "fog" in text:
        score -= 20
        risks.append("visibility/fog risk")
    if "wind" in text:
        score -= 10
        risks.append("wind risk")

    return max(0, min(100, score)), risks or ["no major window-specific risk"]


def timeline_intelligence(question, weather):
    weather = weather or {}
    hourly = weather.get("hourly") or []
    watchman = weather.get("watchman") or {}
    base = int(watchman.get("outdoorIndex", 80) or 80)

    labels = [
        ("now", 0),
        ("30 minutes", 1),
        ("1 hour", 2),
        ("3 hours", 4),
        ("tonight", 8),
        ("tomorrow morning", 12),
    ]

    windows = []

    for label, idx in labels:
        h = hourly[idx] if idx < len(hourly) else {}
        text = _hour_text(h)
        score, risks = _window_score(text, base)

        if score >= 75:
            verdict = "GOOD"
        elif score >= 45:
            verdict = "CAUTION"
        else:
            verdict = "AVOID"

        windows.append({
            "window": label,
            "time": h.get("startTime") if isinstance(h, dict) else None,
            "forecast": h.get("shortForecast") if isinstance(h, dict) else "updating",
            "score": score,
            "verdict": verdict,
            "risks": risks,
        })

    best = sorted(windows, key=lambda x: x["score"], reverse=True)[0] if windows else {}

    return {
        "mode": "Watchman Timeline Intelligence",
        "windows": windows,
        "bestWindow": best,
        "confidence": 82,
        "answer": (
            f"Timeline Intelligence: best current window is {best.get('window','unknown')} "
            f"with score {best.get('score','unknown')}/100 and verdict {best.get('verdict','unknown')}. "
            f"Forecast: {best.get('forecast','updating')}."
        ),
    }
