from datetime import datetime


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return d


MISSION_RULES = {
    "mow": {
        "label": "Mow Grass",
        "max_temp": 90,
        "max_precip": 25,
        "bad_words": ["thunder", "storm", "rain", "showers"],
    },
    "fish": {
        "label": "Fishing",
        "max_temp": 95,
        "max_precip": 35,
        "bad_words": ["thunder", "lightning", "storm"],
    },
    "motorcycle": {
        "label": "Motorcycle Ride",
        "max_temp": 95,
        "max_precip": 20,
        "bad_words": ["rain", "showers", "thunder", "storm", "fog"],
    },
    "travel": {
        "label": "Travel",
        "max_temp": 100,
        "max_precip": 40,
        "bad_words": ["heavy rain", "fog", "flood", "storm"],
    },
    "cookout": {
        "label": "Cookout",
        "max_temp": 92,
        "max_precip": 25,
        "bad_words": ["rain", "showers", "thunder", "storm"],
    },
    "walk": {
        "label": "Walking",
        "max_temp": 88,
        "max_precip": 25,
        "bad_words": ["thunder", "storm", "rain"],
    },
    "roof": {
        "label": "Roof Work",
        "max_temp": 86,
        "max_precip": 15,
        "bad_words": ["rain", "showers", "thunder", "storm", "wind"],
    },
    "drone": {
        "label": "Drone Flight",
        "max_temp": 100,
        "max_precip": 15,
        "bad_words": ["rain", "showers", "thunder", "storm", "wind", "fog"],
    },
}


def _hour_label(start_time):
    try:
        dt = datetime.fromisoformat(str(start_time).replace("Z", "+00:00"))
        return dt.strftime("%a %-I:%M %p")
    except Exception:
        return str(start_time or "Unknown")


def _score_hour(hour, rules):
    temp = _safe_int(hour.get("temperature"), 0)
    precip = _safe_int((hour.get("probabilityOfPrecipitation") or {}).get("value"), 0)
    text = str(hour.get("shortForecast") or "").lower()
    wind = str(hour.get("windSpeed") or "").lower()

    score = 100
    reasons = []

    if temp > rules["max_temp"]:
        penalty = min(35, (temp - rules["max_temp"]) * 3)
        score -= penalty
        reasons.append(f"temperature {temp}° is above preferred limit")

    if precip > rules["max_precip"]:
        penalty = min(40, precip - rules["max_precip"])
        score -= penalty
        reasons.append(f"rain chance {precip}% is above preferred limit")

    for word in rules["bad_words"]:
        if word in text or word in wind:
            score -= 18
            reasons.append(f"{word} signal in forecast")
            break

    if "calm" in wind or "0 mph" in wind or "5 mph" in wind:
        score += 5
        reasons.append("wind looks manageable")

    score = max(0, min(100, int(score)))

    return {
        "time": _hour_label(hour.get("startTime")),
        "rawStartTime": hour.get("startTime"),
        "score": score,
        "temperature": temp,
        "precipChance": precip,
        "forecast": hour.get("shortForecast"),
        "wind": hour.get("windSpeed"),
        "reasons": reasons or ["No major mission concern detected."],
    }


def mission_time_machine(mission, weather):
    weather = weather or {}
    hourly = weather.get("hourly") or []
    mission_key = (mission or "travel").lower().strip()
    rules = MISSION_RULES.get(mission_key, MISSION_RULES["travel"])

    scored = [_score_hour(h, rules) for h in hourly[:24] if isinstance(h, dict)]
    scored = [h for h in scored if h.get("rawStartTime")]

    best = sorted(scored, key=lambda x: x["score"], reverse=True)[:5]
    good = [h for h in scored if h["score"] >= 75]

    if good:
        best_window = f"{good[0]['time']} to {good[-1]['time']}"
        verdict = "WINDOW FOUND"
    elif best:
        best_window = f"Best available: {best[0]['time']}"
        verdict = "LIMITED WINDOW"
    else:
        best_window = "No hourly forecast window available."
        verdict = "NO WINDOW"

    return {
        "mode": "Watchman Mission Time Machine V1",
        "mission": mission_key,
        "missionLabel": rules["label"],
        "verdict": verdict,
        "bestWindow": best_window,
        "bestHours": best,
        "timeline": scored[:12],
        "answer": f"{rules['label']}: {verdict}. {best_window}",
    }
