from datetime import date, datetime, timedelta
import math


def _julian_day(d):
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    return d.day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _sun_time(day, latitude, longitude, zenith=90.833, sunrise=True):
    n = _julian_day(day) - _julian_day(date(day.year, 1, 1)) + 1
    lng_hour = longitude / 15.0
    t = n + ((6 - lng_hour) / 24 if sunrise else (18 - lng_hour) / 24)

    m = (0.9856 * t) - 3.289

    l = m + (1.916 * math.sin(math.radians(m))) + (0.020 * math.sin(math.radians(2 * m))) + 282.634
    l = l % 360

    ra = math.degrees(math.atan(0.91764 * math.tan(math.radians(l))))
    ra = ra % 360

    l_quadrant = math.floor(l / 90) * 90
    ra_quadrant = math.floor(ra / 90) * 90
    ra = ra + (l_quadrant - ra_quadrant)
    ra = ra / 15

    sin_dec = 0.39782 * math.sin(math.radians(l))
    cos_dec = math.cos(math.asin(sin_dec))

    cos_h = (
        math.cos(math.radians(zenith))
        - (sin_dec * math.sin(math.radians(latitude)))
    ) / (cos_dec * math.cos(math.radians(latitude)))

    if cos_h > 1:
        return None
    if cos_h < -1:
        return None

    if sunrise:
        h = 360 - math.degrees(math.acos(cos_h))
    else:
        h = math.degrees(math.acos(cos_h))

    h = h / 15
    local_mean_time = h + ra - (0.06571 * t) - 6.622
    utc_time = (local_mean_time - lng_hour) % 24
    return utc_time


def _format_local_hour(utc_hour, utc_offset_hours):
    if utc_hour is None:
        return "unavailable"

    local_hour = (utc_hour + utc_offset_hours) % 24
    hour = int(local_hour)
    minute = int(round((local_hour - hour) * 60))

    if minute >= 60:
        hour = (hour + 1) % 24
        minute = 0

    suffix = "AM" if hour < 12 else "PM"
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12

    return f"{display_hour}:{minute:02d} {suffix}"


def _parse_requested_day(question):
    q = str(question or "").lower()
    today = date.today()

    if "tomorrow" in q:
        return today + timedelta(days=1)

    if "today" in q or "tonight" in q:
        return today

    # Basic YYYY-MM-DD support.
    for token in str(question or "").replace("/", "-").split():
        token = token.strip(" ?.,!")
        try:
            if len(token) == 10 and token[4] == "-" and token[7] == "-":
                return datetime.strptime(token, "%Y-%m-%d").date()
        except Exception:
            pass

    return today


def solar_times_intelligence(question, weather):
    weather = weather or {}
    location = weather.get("location") or {}

    lat = location.get("lat") or location.get("latitude")
    lon = location.get("lon") or location.get("longitude")

    place = location.get("name") or "this location"

    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return {
            "mode": "Watchman Solar Times Intelligence",
            "answer": "Exact sunrise and sunset times need latitude and longitude for the selected location.",
            "confidence": 40,
            "status": "missing_coordinates",
        }

    requested_day = _parse_requested_day(question)

    # Current Watchman app is operating in Central time for Alabama test data.
    # Future phase can derive the timezone by coordinates.
    utc_offset = -5

    sunrise_utc = _sun_time(requested_day, lat, lon, sunrise=True)
    sunset_utc = _sun_time(requested_day, lat, lon, sunrise=False)

    sunrise = _format_local_hour(sunrise_utc, utc_offset)
    sunset = _format_local_hour(sunset_utc, utc_offset)

    daylight_minutes = None
    if sunrise_utc is not None and sunset_utc is not None:
        diff = (sunset_utc - sunrise_utc) % 24
        daylight_minutes = int(round(diff * 60))

    if daylight_minutes is not None:
        hours = daylight_minutes // 60
        minutes = daylight_minutes % 60
        daylight = f"{hours}h {minutes}m"
    else:
        daylight = "unavailable"

    q = str(question or "").lower()

    if "sunrise" in q or "rise" in q:
        answer = f"Sunrise for {place} on {requested_day} is about {sunrise}."
    elif "sunset" in q or "set" in q:
        answer = f"Sunset for {place} on {requested_day} is about {sunset}."
    elif "daylight" in q:
        answer = f"{place} has about {daylight} of daylight on {requested_day}."
    else:
        answer = f"For {place} on {requested_day}, sunrise is about {sunrise} and sunset is about {sunset}."

    return {
        "mode": "Watchman Solar Times Intelligence",
        "status": "estimated",
        "location": place,
        "date": str(requested_day),
        "sunrise": sunrise,
        "sunset": sunset,
        "daylight": daylight,
        "answer": answer,
        "confidence": 82,
        "note": "Solar time is calculated from coordinates. Timezone handling is V1 and assumes Central time for current Watchman deployment.",
        "whatWouldChangeTheAnswer": [
            "timezone-by-coordinate integration",
            "civil twilight calculation",
            "nautical twilight calculation",
            "astronomical twilight calculation",
            "solar noon calculation",
        ],
    }
