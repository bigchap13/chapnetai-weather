def long_range_planning_intelligence(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []

    days = []

    for item in forecast[:10]:
        if not isinstance(item, dict):
            continue

        name = item.get("name") or "period"
        short = item.get("shortForecast") or "conditions updating"
        temp = item.get("temperature")
        pop = ((item.get("probabilityOfPrecipitation") or {}).get("value"))

        text = short.lower()
        score = 80
        risks = []

        if "thunderstorm" in text or "storm" in text:
            score -= 35
            risks.append("storm risk")
        if "rain" in text or "showers" in text:
            score -= 20
            risks.append("rain risk")
        if temp is not None:
            try:
                t = int(temp)
                if t >= 92:
                    score -= 20
                    risks.append("heat risk")
                if t <= 35:
                    score -= 20
                    risks.append("cold risk")
            except Exception:
                pass
        if pop is not None:
            try:
                if int(pop) >= 50:
                    score -= 15
                    risks.append("higher precipitation chance")
            except Exception:
                pass

        score = max(0, min(100, score))

        if score >= 75:
            verdict = "BEST"
        elif score >= 50:
            verdict = "OK"
        else:
            verdict = "AVOID"

        days.append({
            "name": name,
            "forecast": short,
            "temperature": temp,
            "precipChance": pop,
            "score": score,
            "verdict": verdict,
            "risks": risks or ["no major planning risk"],
        })

    best = sorted(days, key=lambda x: x["score"], reverse=True)[:3]

    return {
        "mode": "Watchman Long-Range Planning Intelligence",
        "confidence": 76,
        "bestWindows": best,
        "allWindows": days,
        "recommendation": "Use the highest-scoring windows for outdoor plans and recheck Watchman as the date gets closer.",
        "whatWouldChangeTheAnswer": [
            "Forecast trend changes",
            "Rain timing shifts",
            "New alerts",
            "Temperature forecast changes",
        ],
    }
