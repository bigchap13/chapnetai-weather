from datetime import date, datetime, timedelta
import math

SYNODIC_MONTH = 29.53058867
KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14)


PHASES = [
    ("New Moon", 0.0),
    ("First Quarter", 0.25),
    ("Full Moon", 0.5),
    ("Last Quarter", 0.75),
]


def _moon_age_days(day):
    dt = datetime(day.year, day.month, day.day, 12, 0)
    days = (dt - KNOWN_NEW_MOON).total_seconds() / 86400.0
    return days % SYNODIC_MONTH


def _phase_fraction(day):
    return _moon_age_days(day) / SYNODIC_MONTH


def _phase_name(frac):
    if frac < 0.03 or frac > 0.97:
        return "New Moon"
    if frac < 0.22:
        return "Waxing Crescent"
    if frac < 0.28:
        return "First Quarter"
    if frac < 0.47:
        return "Waxing Gibbous"
    if frac < 0.53:
        return "Full Moon"
    if frac < 0.72:
        return "Waning Gibbous"
    if frac < 0.78:
        return "Last Quarter"
    return "Waning Crescent"


def _illumination(frac):
    return round((1 - math.cos(2 * math.pi * frac)) / 2 * 100)


def _next_phase(target_fraction, start=None):
    start = start or date.today()
    best = None
    best_error = 999

    for i in range(0, 45):
        d = start + timedelta(days=i)
        frac = _phase_fraction(d)
        error = abs(frac - target_fraction)
        error = min(error, 1 - error)

        if error < best_error:
            best = d
            best_error = error

    return best


def _requested_day(question):
    q = str(question or "").lower()
    today = date.today()

    if "tomorrow" in q:
        return today + timedelta(days=1)
    if "today" in q or "tonight" in q:
        return today

    for token in str(question or "").replace("/", "-").split():
        token = token.strip(" ?.,!")
        try:
            if len(token) == 10 and token[4] == "-" and token[7] == "-":
                return datetime.strptime(token, "%Y-%m-%d").date()
        except Exception:
            pass

    return today


def moon_phase_intelligence(question, weather=None):
    q = str(question or "").lower()
    day = _requested_day(question)

    frac = _phase_fraction(day)
    age = round(_moon_age_days(day), 1)
    phase = _phase_name(frac)
    illumination = _illumination(frac)

    next_new = _next_phase(0.0, day)
    next_first = _next_phase(0.25, day)
    next_full = _next_phase(0.5, day)
    next_last = _next_phase(0.75, day)

    if "full moon" in q:
        answer = f"The next full moon is around {next_full}."
    elif "new moon" in q:
        answer = f"The next new moon is around {next_new}."
    elif "first quarter" in q:
        answer = f"The next first quarter moon is around {next_first}."
    elif "last quarter" in q:
        answer = f"The next last quarter moon is around {next_last}."
    elif "moonlight" in q or "meteor" in q:
        if illumination >= 70:
            answer = f"Moonlight may interfere. The moon is about {illumination}% illuminated in the {phase} phase."
        elif illumination >= 35:
            answer = f"Moonlight may have some impact. The moon is about {illumination}% illuminated in the {phase} phase."
        else:
            answer = f"Moonlight should be limited. The moon is about {illumination}% illuminated in the {phase} phase."
    else:
        answer = f"The moon on {day} is {phase}, about {illumination}% illuminated, and about {age} days old."

    return {
        "mode": "Watchman Moon Phase Intelligence",
        "status": "active",
        "date": str(day),
        "phase": phase,
        "illuminationPercent": illumination,
        "moonAgeDays": age,
        "nextNewMoon": str(next_new),
        "nextFirstQuarter": str(next_first),
        "nextFullMoon": str(next_full),
        "nextLastQuarter": str(next_last),
        "answer": answer,
        "confidence": 78,
        "note": "V1 uses astronomical approximation. Future versions can integrate high-precision ephemeris data.",
        "whatWouldChangeTheAnswer": [
            "high-precision ephemeris integration",
            "local moonrise and moonset integration",
            "timezone-specific lunar phase timing",
        ],
    }
