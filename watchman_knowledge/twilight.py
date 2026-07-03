from datetime import date, datetime, timedelta
import math


def _julian_day(d):
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    return d.day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _sun_time(day, latitude, longitude, zenith, sunrise=True):
    n = _julian_day(day) - _julian_day(date(day.year, 1, 1)) + 1
    lng_hour = longitude / 15.0
    t = n + ((6 - lng_hour) / 24 if sunrise else (18 - lng_hour) / 24)

    m = (0.9856 * t) - 3.289
    l = m + (1.916 * math.sin(math.radians(m))) + (0.020 * math.sin(math.radians(2 * m))) + 282.634
    l = l % 360

    ra = math.degrees(math.atan(0.91764 * math.tan(math.radians(l))))
    ra = ra % 360

    lq = math.floor(l / 90) * 90
    rq = math.floor(ra / 90) * 90
    ra = (ra + (lq - rq)) / 15

    sin_dec = 0.39782 * math.sin(math.radians(l))
    cos_dec = math.cos(math.asin(sin_dec))

    cos_h = (math.cos(math.radians(zenith)) - (sin_dec * math.sin(math.radians(latitude)))) / (
        cos_dec * math.cos(math.radians(latitude))
    )

    if cos_h > 1 or cos_h < -1:
        return None

    h = 360 - math.degrees(math.acos(cos_h)) if sunrise else math.degrees(math.acos(cos_h))
    h = h / 15

    local_mean = h + ra - (0.06571 * t) - 6.622
    return (local_mean - lng_hour) % 24


def _fmt(utc_hour, offset=-5):
    if utc_hour is None:
        return "unavailable"

    local = (utc_hour + offset) % 24
    hour = int(local)
    minute = int(round((local - hour) * 60))

    if minute >= 60:
        hour = (hour + 1) % 24
        minute = 0

    suffix = "AM" if hour < 12 else "PM"
    display = hour % 12 or 12
    return f"{display}:{minute:02d} {suffix}"


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


def twilight_intelligence(question, weather):
    weather = weather or {}
    location = weather.get("location") or {}
    place = location.get("name") or "this location"

    lat = location.get("lat") or location.get("latitude")
    lon = location.get("lon") or location.get("longitude")

    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return {
            "mode": "Watchman Twilight Intelligence",
            "answer": "Twilight Intelligence needs latitude and longitude for the selected location.",
            "confidence": 40,
        }

    day = _requested_day(question)

    sunrise = _fmt(_sun_time(day, lat, lon, 90.833, True))
    sunset = _fmt(_sun_time(day, lat, lon, 90.833, False))

    civil_begin = _fmt(_sun_time(day, lat, lon, 96, True))
    civil_end = _fmt(_sun_time(day, lat, lon, 96, False))

    nautical_begin = _fmt(_sun_time(day, lat, lon, 102, True))
    nautical_end = _fmt(_sun_time(day, lat, lon, 102, False))

    astro_begin = _fmt(_sun_time(day, lat, lon, 108, True))
    astro_end = _fmt(_sun_time(day, lat, lon, 108, False))

    solar_noon = _fmt(((_sun_time(day, lat, lon, 90.833, True) or 0) + (_sun_time(day, lat, lon, 90.833, False) or 0)) / 2)

    q = str(question or "").lower()

    if "golden hour" in q:
        answer = f"Golden hour for {place} on {day} is roughly after sunrise near {sunrise} and before sunset near {sunset}."
    elif "blue hour" in q:
        answer = f"Blue hour for {place} on {day} is roughly around civil twilight: {civil_begin} before sunrise and {civil_end} after sunset."
    elif "astronomical" in q or "dark" in q or "milky way" in q:
        answer = f"Astronomical darkness for {place} on {day} begins around {astro_end} and ends around {astro_begin}."
    elif "civil" in q:
        answer = f"Civil twilight for {place} on {day} begins around {civil_begin} and ends around {civil_end}."
    elif "nautical" in q:
        answer = f"Nautical twilight for {place} on {day} begins around {nautical_begin} and ends around {nautical_end}."
    elif "solar noon" in q:
        answer = f"Solar noon for {place} on {day} is about {solar_noon}."
    else:
        answer = f"For {place} on {day}: civil twilight {civil_begin} to {civil_end}, nautical twilight {nautical_begin} to {nautical_end}, astronomical twilight {astro_begin} to {astro_end}."

    return {
        "mode": "Watchman Twilight Intelligence",
        "status": "estimated",
        "location": place,
        "date": str(day),
        "sunrise": sunrise,
        "sunset": sunset,
        "civilTwilightBegin": civil_begin,
        "civilTwilightEnd": civil_end,
        "nauticalTwilightBegin": nautical_begin,
        "nauticalTwilightEnd": nautical_end,
        "astronomicalTwilightBegin": astro_begin,
        "astronomicalTwilightEnd": astro_end,
        "solarNoon": solar_noon,
        "answer": answer,
        "confidence": 80,
        "note": "V1 estimates twilight from coordinates and assumes Central time for current deployment.",
        "whatWouldChangeTheAnswer": [
            "timezone-by-coordinate integration",
            "higher precision solar ephemeris",
            "terrain horizon correction",
        ],
    }
