WATCHMAN_WEATHER_VERSION = "Watchman V108"


def _flat(v):
    out = []

    def walk(x):
        if isinstance(x, dict):
            for y in x.values():
                walk(y)
        elif isinstance(x, list):
            for y in x:
                walk(y)
        elif x is not None:
            out.append(str(x))

    walk(v)
    return " ".join(out).lower()


def evaluate_weather_risk(payload=None):
    text = _flat(payload or {})
    checks = [
        ("tornado warning", 70, "Tornado warning"),
        ("tornado", 50, "Tornado threat"),
        ("severe thunderstorm warning", 50, "Severe thunderstorm warning"),
        ("severe thunderstorm", 35, "Severe thunderstorm threat"),
        ("flash flood warning", 55, "Flash flood warning"),
        ("flash flood", 40, "Flash flooding threat"),
        ("flood watch", 30, "Flood watch"),
        ("flood", 25, "Flooding threat"),
        ("winter storm", 35, "Winter storm threat"),
        ("ice", 25, "Ice threat"),
        ("snow", 15, "Snow threat"),
        ("extreme heat", 30, "Extreme heat threat"),
        ("heat advisory", 25, "Heat advisory"),
        ("high wind", 30, "High wind threat"),
        ("dense fog", 15, "Dense fog threat"),
    ]
    hazards = []
    score = 0
    for key, points, label in checks:
        if key in text and label not in hazards:
            hazards.append(label)
            score += points
    level = "critical" if score >= 70 else "high" if score >= 40 else "elevated" if score >= 20 else "guarded" if score else "normal"
    return {
        "version": WATCHMAN_WEATHER_VERSION,
        "risk_level": level,
        "score": score,
        "hazards": hazards,
        "summary": WATCHMAN_WEATHER_VERSION + " weather risk analysis complete.",
        "recommended_actions": [
            "Monitor official NWS alerts.",
            "Keep weather notifications enabled.",
            "Avoid unnecessary travel during active warnings.",
        ],
    }
