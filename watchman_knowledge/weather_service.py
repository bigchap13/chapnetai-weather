def normalize_place(place, fallback="Jasper, Alabama"):
    place = (place or fallback).strip() or fallback
    place = place.replace(",", ", ")
    while "  " in place:
        place = place.replace("  ", " ")
    return place


def weather_lookup_for_place(place, geocode_fn, fetch_weather_fn):
    place = normalize_place(place)

    candidates = [place]
    if "," not in place:
        state_suffixes = [
            " Alabama", " Alaska", " Arizona", " Arkansas", " California", " Colorado",
            " Connecticut", " Delaware", " Florida", " Georgia", " Idaho", " Illinois",
            " Indiana", " Iowa", " Kansas", " Kentucky", " Louisiana", " Maine",
            " Maryland", " Massachusetts", " Michigan", " Minnesota", " Mississippi",
            " Missouri", " Montana", " Nebraska", " Nevada", " New Hampshire",
            " New Jersey", " New Mexico", " New York", " North Carolina",
            " North Dakota", " Ohio", " Oklahoma", " Oregon", " Pennsylvania",
            " Rhode Island", " South Carolina", " South Dakota", " Tennessee",
            " Texas", " Utah", " Vermont", " Virginia", " Washington",
            " West Virginia", " Wisconsin", " Wyoming",
        ]
        for suffix in state_suffixes:
            if place.lower().endswith(suffix.lower()):
                city_only = place[:-len(suffix)].strip()
                if city_only:
                    candidates.append(city_only)
                break

    geo = None
    resolved_place = place
    for candidate in candidates:
        geo = geocode_fn(candidate)
        if geo:
            resolved_place = candidate
            break

    if not geo:
        return {
            "error": "geocode_failed",
            "place": place,
        }

    place = resolved_place

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


def weather_lookup_for_gps(label, lat, lon, fetch_weather_fn, fallback_place=None):
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

    # Critical: do not silently fall back route GPS weather to Jasper.
    # Route planning must score each sampled road point from that point's own GPS.
    if isinstance(weather, dict) and "error" in weather and fallback_place:
        weather = fetch_weather_fn(fallback_place)

    if isinstance(weather, dict):
        weather.setdefault("_lookup", {
            "place": label,
            "lat": lat,
            "lon": lon,
            "gps": True,
        })

    return weather
