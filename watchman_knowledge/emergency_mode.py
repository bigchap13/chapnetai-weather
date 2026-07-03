US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _alert_text(alert):
    if not isinstance(alert, dict):
        return ""
    return " ".join([
        str(alert.get("event", "")),
        str(alert.get("headline", "")),
        str(alert.get("description", "")),
        str(alert.get("instruction", "")),
        str(alert.get("areaDesc", "")),
        str(alert.get("area", "")),
        str(alert.get("geocode", "")),
        str(alert.get("severity", "")),
        str(alert.get("urgency", "")),
    ]).lower()


def _location_text(weather):
    loc = (weather or {}).get("location") or {}
    parts = []
    if isinstance(loc, dict):
        parts.extend(str(v) for v in loc.values())
    parts.append(str((weather or {}).get("place", "")))
    parts.append(str((weather or {}).get("requestedPlace", "")))
    return " ".join(parts).lower()


def _derive_state(weather):
    text = _location_text(weather)

    for name, abbr in US_STATES.items():
        if name in text:
            return name, abbr
        if f" {abbr.lower()} " in f" {text} ":
            return name, abbr

    return None, None


def _alert_matches_scope(alert, weather):
    alert_text = _alert_text(alert)
    state_name, state_abbr = _derive_state(weather)

    # Best case: NWS/geocoder already returned alerts for selected/GPS location.
    # If there is no state marker inside the alert payload, accept it as local.
    all_state_words = list(US_STATES.keys()) + [v.lower() for v in US_STATES.values()]
    has_any_state_marker = any(f" {s} " in f" {alert_text} " or s in alert_text for s in all_state_words)

    if not has_any_state_marker:
        return True

    # If state was derived, require the alert to match that state.
    if state_name and (state_name in alert_text or f" {state_abbr.lower()} " in f" {alert_text} "):
        return True

    return False


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
    alerts = weather.get("alerts") or []
    state_name, state_abbr = _derive_state(weather)

    qualifying = []

    for alert in alerts:
        text = _alert_text(alert)
        kind, event, level = _hazard_type(text)
        if kind and _alert_matches_scope(alert, weather):
            qualifying.append({
                "kind": kind,
                "event": event,
                "level": level,
                "scope": state_abbr or state_name or "local_selected_location",
            })

    radar_arrival = "unknown"
    if isinstance(radar_result, dict):
        radar_arrival = radar_result.get("arrivalEstimate") or "unknown"

    if not qualifying:
        return {
            "mode": "Watchman Emergency Mode",
            "active": False,
            "scope": state_abbr or state_name or "selected_location",
            "answer": (
                "Emergency Mode is not active. No qualifying life-safety alert is detected "
                "for the selected GPS/place/state scope."
            ),
            "confidence": 82,
        }

    chosen = qualifying[0]
    kind = chosen["kind"]
    event = chosen["event"]
    level = chosen["level"]
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
        f"Scope: {chosen['scope']}. "
        f"Threat level: {level}. "
        f"Radar arrival estimate: {radar_arrival}. "
        f"Instructions: {'; '.join(instructions)} "
        f"Qualifying alert count: {len(qualifying)}."
    )

    return {
        "mode": "Watchman Emergency Mode",
        "active": True,
        "scope": chosen["scope"],
        "level": level,
        "event": event,
        "hazardType": kind,
        "confidence": confidence,
        "radarArrivalEstimate": radar_arrival,
        "qualifyingAlertCount": len(qualifying),
        "instructions": instructions,
        "answer": answer,
        "officialGuidanceRule": "Official National Weather Service and emergency management instructions take priority.",
    }
