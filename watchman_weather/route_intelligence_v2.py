from datetime import datetime

def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d

def route_intelligence_v2(question, weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    forecast = weather.get("forecast") or []
    alerts = weather.get("alerts") or []

    travel = _safe_int(watchman.get("travelIndex"), 75)
    threat = _safe_int(watchman.get("threatScore"), 0)
    precip = _safe_int(watchman.get("precipChance"), 0)

    departures = [
        ("Now", travel - threat),
        ("1 hour", travel - max(threat - 5, 0)),
        ("2 hours", travel - max(threat - 10, 0)),
        ("Tomorrow morning", min(100, travel + 5)),
    ]

    departures = [(n, max(0, min(100, s))) for n, s in departures]
    best = max(departures, key=lambda x: x[1])
    worst = min(departures, key=lambda x: x[1])

    first = forecast[0] if forecast else {}

    if best[1] >= 80:
        verdict = "GO"
    elif best[1] >= 50:
        verdict = "CAUTION"
    else:
        verdict = "DELAY"

    return {
        "mode": "Watchman Route Intelligence V2",
        "verdict": verdict,
        "bestDeparture": best[0],
        "bestScore": best[1],
        "worstDeparture": worst[0],
        "worstScore": worst[1],
        "arrivalForecast": first.get("shortForecast", "Unknown"),
        "alerts": len(alerts),
        "generated": datetime.utcnow().isoformat() + "Z",
        "answer": (
            f"Route Intelligence V2: {verdict}. "
            f"Best departure: {best[0]} ({best[1]}/100). "
            f"Worst departure: {worst[0]} ({worst[1]}/100). "
            f"Arrival weather: {first.get('shortForecast','Unknown')}."
        )
    }
