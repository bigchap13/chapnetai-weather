def _text_blob(weather):
    weather = weather or {}
    parts = []

    for alert in weather.get("alerts") or []:
        if isinstance(alert, dict):
            parts.extend([
                str(alert.get("event", "")),
                str(alert.get("headline", "")),
                str(alert.get("description", "")),
                str(alert.get("instruction", "")),
                str(alert.get("severity", "")),
                str(alert.get("urgency", "")),
            ])

    watchman = weather.get("watchman") or {}
    parts.extend([
        str(watchman.get("threatLevel", "")),
        str(watchman.get("threatScore", "")),
        str(watchman.get("aiBriefing", "")),
        str(watchman.get("aiWeatherNarrative", "")),
    ])

    return " ".join(parts).lower()


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _hazard_type(text):
    if "tornado emergency" in text:
        return "tornado_emergency", "TORNADO EMERGENCY", "life_threatening"
    if "tornado warning" in text or "tornado" in text:
        return "tornado_warning", "TORNADO WARNING", "life_threatening"
    if "flash flood emergency" in text:
        return "flash_flood_emergency", "FLASH FLOOD EMERGENCY", "life_threatening"
    if "flash flood warning" in text:
        return "flash_flood_warning", "FLASH FLOOD WARNING", "dangerous"
    if "severe thunderstorm warning" in text:
        if "destructive" in text or "considerable" in text:
            return "destructive_thunderstorm", "DESTRUCTIVE SEVERE THUNDERSTORM WARNING", "dangerous"
        return "severe_thunderstorm", "SEVERE THUNDERSTORM WARNING", "dangerous"
    if "extreme wind warning" in text:
        return "extreme_wind", "EXTREME WIND WARNING", "life_threatening"
    if "hurricane warning" in text:
        return "hurricane", "HURRICANE WARNING", "life_threatening"
    if "blizzard warning" in text:
        return "blizzard", "BLIZZARD WARNING", "dangerous"
    if "winter storm warning" in text:
        return "winter_storm", "WINTER STORM WARNING", "dangerous"
    if "excessive heat warning" in text:
        return "excessive_heat", "EXCESSIVE HEAT WARNING", "dangerous"
    return None, None, None


def _instructions(kind):
    if kind in ["tornado_emergency", "tornado_warning"]:
        return [
            "Seek shelter immediately.",
            "Go to the lowest floor available.",
            "Move to an interior room away from windows.",
            "Protect your head and neck.",
            "Do not remain in a vehicle or mobile home if safer shelter is available.",
        ]

    if kind in ["flash_flood_emergency", "flash_flood_warning"]:
        return [
            "Do not drive through water-covered roads.",
            "Avoid low-water crossings.",
            "Move to higher ground if flooding is nearby.",
            "Delay travel until flood risk drops.",
            "Follow official evacuation or emergency instructions.",
        ]

    if kind in ["severe_thunderstorm", "destructive_thunderstorm", "extreme_wind", "hurricane"]:
        return [
            "Move indoors immediately.",
            "Stay away from windows.",
            "Avoid travel until the warning passes.",
            "Secure loose outdoor objects only if it is safe to do so.",
            "Prepare for power outages.",
        ]

    if kind in ["blizzard", "winter_storm"]:
        return [
            "Delay travel if possible.",
            "Watch for ice, low visibility, and blocked roads.",
            "Keep emergency supplies available.",
            "Avoid unnecessary exposure.",
            "Check official road conditions before leaving.",
        ]

    if kind == "excessive_heat":
        return [
            "Limit outdoor activity.",
            "Hydrate frequently.",
            "Use cooling breaks and shade.",
            "Check on children, elderly people, pets, and outdoor workers.",
            "Watch for heat illness symptoms.",
        ]

    return [
        "Stay weather-aware.",
        "Follow official emergency instructions.",
        "Keep Watchman open for updates.",
    ]


def emergency_mode(question, weather, radar_result=None):
    weather = weather or {}
    watchman = weather.get("watchman") or {}
    alerts = weather.get("alerts") or []
    text = _text_blob(weather)

    threat_score = _safe_int(watchman.get("threatScore"), 0)
    kind, event, level = _hazard_type(text)

    radar_score = 0
    radar_arrival = "unknown"
    if isinstance(radar_result, dict):
        radar_score = _safe_int(radar_result.get("score"), 0)
        radar_arrival = radar_result.get("arrivalEstimate") or "unknown"

    active = False
    if kind:
        active = True
    elif threat_score >= 75:
        active = True
        kind = "watchman_high_threat"
        event = "WATCHMAN HIGH THREAT"
        level = "dangerous"
    elif radar_score >= 90:
        active = True
        kind = "radar_high_threat"
        event = "RADAR HIGH THREAT"
        level = "dangerous"

    if not active:
        return {
            "mode": "Watchman Emergency Mode",
            "active": False,
            "answer": "Emergency Mode is not active. No life-threatening Watchman emergency trigger is currently detected.",
            "confidence": 82,
        }

    instructions = _instructions(kind)

    if level == "life_threatening":
        lead = "WATCHMAN EMERGENCY MODE ACTIVE"
        action = "Take protective action immediately."
        confidence = 96
    else:
        lead = "WATCHMAN DANGEROUS WEATHER MODE ACTIVE"
        action = "Avoid unnecessary risk and follow official guidance."
        confidence = 90

    answer = (
        f"{lead}: {event}. {action} "
        f"Threat level: {level}. "
        f"Radar arrival estimate: {radar_arrival}. "
        f"Instructions: {'; '.join(instructions)} "
        f"Official alert count: {len(alerts)}."
    )

    return {
        "mode": "Watchman Emergency Mode",
        "active": True,
        "level": level,
        "event": event,
        "hazardType": kind,
        "confidence": confidence,
        "radarArrivalEstimate": radar_arrival,
        "officialAlertCount": len(alerts),
        "instructions": instructions,
        "answer": answer,
        "officialGuidanceRule": "Official National Weather Service and emergency management instructions take priority.",
    }
