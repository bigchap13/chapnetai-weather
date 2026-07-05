def normalize_place(place, fallback="Jasper, Alabama"):
    place = (place or fallback).strip() or fallback
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")
    return place


def weather_lookup_for_place(place, geocode_fn, fetch_weather_fn):
    place = normalize_place(place)
    geo = geocode_fn(place)

    if not geo:
        return {
            "error": "geocode_failed",
            "place": place,
        }

    lat = geo.get("lat") or geo.get("latitude")
    lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")

    if lat is None or lon is None:
        return {
            "error": "geocode_coordinates_missing",
            "place": place,
            "geocode": geo,
        }

    weather = fetch_weather_fn(place)

    if isinstance(weather, dict):
        weather.setdefault("_lookup", {
            "place": place,
            "lat": lat,
            "lon": lon,
            "geocode": geo,
        })

    return weather


def weather_lookup_for_gps(label, lat, lon, fetch_weather_fn, fallback_place="Jasper, Alabama"):
    label = normalize_place(label, "GPS Location")

    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return {
            "error": "missing_or_invalid_gps",
            "required": "lat and lon query parameters",
        }

    weather = fetch_weather_fn(f"{lat},{lon}")

    if isinstance(weather, dict) and "error" in weather:
        weather = fetch_weather_fn(fallback_place)

    if isinstance(weather, dict):
        weather.setdefault("_lookup", {
            "place": label,
            "lat": lat,
            "lon": lon,
            "gps": True,
        })

    return weather
