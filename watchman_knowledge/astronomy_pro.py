from datetime import datetime

METEOR_SHOWERS = [
    {"name": "Quadrantids", "months": [1], "peak": "early January", "strength": "strong", "notes": "Short sharp peak; best after midnight."},
    {"name": "Lyrids", "months": [4], "peak": "late April", "strength": "moderate", "notes": "Known for occasional bright meteors."},
    {"name": "Eta Aquariids", "months": [5], "peak": "early May", "strength": "moderate", "notes": "Best before dawn; associated with Halley's Comet."},
    {"name": "Delta Aquariids", "months": [7, 8], "peak": "late July", "strength": "moderate", "notes": "Best from dark southern skies."},
    {"name": "Perseids", "months": [8], "peak": "mid August", "strength": "major", "notes": "One of the most famous and reliable meteor showers."},
    {"name": "Orionids", "months": [10], "peak": "late October", "strength": "moderate", "notes": "Fast meteors; associated with Halley's Comet."},
    {"name": "Leonids", "months": [11], "peak": "mid November", "strength": "variable", "notes": "Sometimes produces outbursts."},
    {"name": "Geminids", "months": [12], "peak": "mid December", "strength": "major", "notes": "Often one of the strongest showers of the year."},
    {"name": "Ursids", "months": [12], "peak": "late December", "strength": "minor", "notes": "Usually modest but worth watching under dark skies."},
]


def _current_month():
    return datetime.now().month


def _sky_score(weather):
    weather = weather or {}
    forecast = weather.get("forecast") or []
    hourly = weather.get("hourly") or []

    text = " ".join(
        str(x.get("shortForecast", "")) + " " + str(x.get("detailedForecast", ""))
        for x in forecast[:4] if isinstance(x, dict)
    ).lower()

    text += " " + " ".join(
        str(x.get("shortForecast", ""))
        for x in hourly[:12] if isinstance(x, dict)
    ).lower()

    score = 65
    risks = []

    if any(k in text for k in ["clear", "mostly clear"]):
        score += 20
        risks.append("clear sky signal")
    if any(k in text for k in ["cloudy", "overcast", "fog", "rain", "showers", "thunderstorm"]):
        score -= 35
        risks.append("cloud, fog, rain, or storm signal")

    score = max(0, min(100, score))
    return score, risks or ["no major sky visibility signal detected"]


def astronomy_pro_intelligence(question, weather):
    q = str(question or "").lower()
    month = _current_month()
    sky_score, sky_risks = _sky_score(weather)

    active = [s for s in METEOR_SHOWERS if month in s["months"]]
    upcoming = []

    for s in METEOR_SHOWERS:
        first_month = s["months"][0]
        if first_month >= month:
            upcoming.append(s)

    if not upcoming:
        upcoming = METEOR_SHOWERS[:3]

    named = None
    for shower in METEOR_SHOWERS:
        if shower["name"].lower() in q:
            named = shower
            break

    if named:
        target = named
        answer = f"{target['name']} meteor shower: peak is usually {target['peak']}. Strength: {target['strength']}. {target['notes']}"
    elif "next" in q:
        target = upcoming[0]
        answer = f"The next major Watchman meteor shower target is {target['name']}, usually peaking {target['peak']}. Strength: {target['strength']}."
    elif active:
        names = ", ".join(s["name"] for s in active)
        answer = f"Watchman meteor calendar shows active seasonal meteor shower window(s): {names}."
    else:
        target = upcoming[0]
        answer = f"No major meteor shower is flagged for the current month. Next key target: {target['name']} around {target['peak']}."

    if sky_score >= 75:
        viewing = "Viewing conditions look favorable if light pollution and moonlight are low."
    elif sky_score >= 45:
        viewing = "Viewing may be possible, but sky conditions could interfere."
    else:
        viewing = "Viewing is not favored by current sky conditions."

    return {
        "mode": "Watchman Astronomy Pro",
        "answer": answer,
        "viewingAssessment": viewing,
        "skyScore": sky_score,
        "confidence": 74,
        "skyRisks": sky_risks,
        "activeShowers": active,
        "nextShowers": upcoming[:3],
        "famousShowers": ["Perseids", "Geminids", "Quadrantids", "Leonids", "Orionids"],
        "watchTips": [
            "Best meteor viewing is usually after midnight and before dawn.",
            "Get away from city lights.",
            "Give your eyes 20 to 30 minutes to adjust.",
            "Avoid bright phone screens.",
            "Clouds, fog, moonlight, and storms can ruin visibility.",
        ],
        "whatWouldChangeTheAnswer": [
            "exact annual peak calendar integration",
            "moon phase integration",
            "cloud forecast changes",
            "fog forecast changes",
            "local light pollution profile",
        ],
    }
