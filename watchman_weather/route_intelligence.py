import re


def _extract_route(question):
    q = str(question or "")
    low = q.lower()

    patterns = [
        r"from\s+(.+?)\s+to\s+(.+?)(?:\?|$)",
        r"drive\s+(.+?)\s+to\s+(.+?)(?:\?|$)",
        r"route\s+(.+?)\s+to\s+(.+?)(?:\?|$)",
    ]

    for pat in patterns:
        m = re.search(pat, low)
        if m:
            start = m.group(1).strip(" .,?")
            end = m.group(2).strip(" .,?")
            if start and end:
                return start.title(), end.title()

    return None, None


def route_intelligence(question, weather):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []

    start, end = _extract_route(question)

    precip = watchman.get("precipChance")
    travel_index = watchman.get("travelIndex", 75)
    threat = watchman.get("threatScore", 0)

    try:
        travel_index = int(travel_index)
    except Exception:
        travel_index = 75

    try:
        threat = int(threat)
    except Exception:
        threat = 0

    route_score = travel_index

    hazards = []
    if alerts:
        route_score -= 15
        hazards.append(f"{len(alerts)} active alert(s)")
    if threat >= 25:
        route_score -= 20
        hazards.append("elevated Watchman threat score")
    if precip is not None:
        try:
            if int(precip) >= 40:
                route_score -= 15
                hazards.append("higher precipitation chance")
        except Exception:
            pass

    route_score = max(0, min(100, route_score))

    if route_score >= 75:
        verdict = "GO"
        recommendation = "Route looks usable. Recheck Watchman before departure."
    elif route_score >= 45:
        verdict = "CAUTION"
        recommendation = "Route is possible, but conditions may affect timing or visibility."
    else:
        verdict = "DELAY"
        recommendation = "Delay if possible or choose a safer departure window."

    first = forecast[0] if forecast and isinstance(forecast[0], dict) else {}
    next_hour = hourly[0] if hourly and isinstance(hourly[0], dict) else {}

    route_label = f"{start} to {end}" if start and end else "selected route"

    return {
        "mode": "Watchman Route Intelligence",
        "route": route_label,
        "start": start,
        "destination": end,
        "verdict": verdict,
        "score": route_score,
        "confidence": 76,
        "recommendation": recommendation,
        "hazards": hazards or ["no major route hazard detected from current destination weather"],
        "arrivalWeatherProxy": first.get("shortForecast") or next_hour.get("shortForecast") or "conditions updating",
        "answer": (
            f"Route Intelligence for {route_label}: {verdict} ({route_score}/100). "
            f"{recommendation} Hazards: {'; '.join(hazards or ['no major route hazard detected from current destination weather'])}. "
            f"Arrival weather proxy: {first.get('shortForecast') or next_hour.get('shortForecast') or 'conditions updating'}."
        ),
        "note": "V1 evaluates route intent using origin/destination text and destination weather. Full route corridor sampling is next phase.",
    }
