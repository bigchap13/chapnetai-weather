from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from watchman_knowledge.weather_service import weather_lookup_for_gps, weather_lookup_for_place


def _num(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _text(v: Any) -> str:
    return str(v or "").strip()


def _dig(obj: Any, keys: List[str]) -> Any:
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _find_lat_lon(obj: Any) -> Tuple[Optional[float], Optional[float]]:
    if not isinstance(obj, dict):
        return None, None

    candidates = [
        ("lat", "lon"),
        ("latitude", "longitude"),
        ("Lat", "Lon"),
    ]

    for a, b in candidates:
        lat = _num(obj.get(a))
        lon = _num(obj.get(b))
        if lat is not None and lon is not None:
            return lat, lon

    nested_paths = [
        ["location"],
        ["geo"],
        ["coordinates"],
        ["point"],
        ["place"],
    ]

    for path in nested_paths:
        child = _dig(obj, path)
        lat, lon = _find_lat_lon(child)
        if lat is not None and lon is not None:
            return lat, lon

    return None, None


def _geocode_destination(destination: str) -> Dict[str, Any]:
    import json
    import urllib.parse
    import urllib.request

    q = urllib.parse.urlencode({"format": "json", "limit": "1", "q": destination})
    url = "https://nominatim.openstreetmap.org/search?" + q

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ChapNetAI-Watchman-Route-Planner/1.0"
        },
    )

    with urllib.request.urlopen(req, timeout=12) as res:
        data = json.loads(res.read().decode("utf-8"))

    if not data:
        return {"ok": False, "error": "destination_not_found", "destination": destination}

    hit = data[0]
    lat = _num(hit.get("lat"))
    lon = _num(hit.get("lon"))

    if lat is None or lon is None:
        return {"ok": False, "error": "destination_coordinates_not_found", "destination": destination}

    return {
        "ok": True,
        "destination": destination,
        "lat": lat,
        "lon": lon,
        "displayName": hit.get("display_name") or destination,
        "source": "openstreetmap_nominatim",
    }


def _destination_to_gps(destination: str) -> Dict[str, Any]:
    destination = _text(destination)
    if not destination:
        return {"ok": False, "error": "destination_required"}

    weather = None

    try:
        weather = weather_lookup_for_place(destination)
        lat, lon = _find_lat_lon(weather)
        if lat is not None and lon is not None:
            return {
                "ok": True,
                "destination": destination,
                "lat": lat,
                "lon": lon,
                "weather": weather,
                "source": "weather_lookup_for_place",
            }
    except Exception:
        pass

    try:
        geo = _geocode_destination(destination)
        if geo.get("ok"):
            return {
                "ok": True,
                "destination": destination,
                "lat": geo["lat"],
                "lon": geo["lon"],
                "displayName": geo.get("displayName") or destination,
                "weather": weather or {},
                "source": geo.get("source"),
            }
        return geo
    except Exception as exc:
        return {
            "ok": False,
            "error": "destination_lookup_failed",
            "destination": destination,
            "details": str(exc)[:300],
        }


def _distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _sample_points(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, count: int) -> List[Dict[str, Any]]:
    count = max(3, min(int(count or 5), 12))
    points = []
    for i in range(count):
        t = i / (count - 1)
        lat = origin_lat + (dest_lat - origin_lat) * t
        lon = origin_lon + (dest_lon - origin_lon) * t
        points.append({
            "index": i + 1,
            "progress": round(t, 3),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
        })
    return points


def _route_weather_at_eta(weather: Dict[str, Any], eta_minutes: Any) -> Dict[str, Any]:
    weather = weather if isinstance(weather, dict) else {}

    try:
        eta = max(0, float(eta_minutes or 0))
    except Exception:
        eta = 0

    hourly = weather.get("hourly") or []
    if not isinstance(hourly, list) or not hourly:
        return weather

    idx = int(round(eta / 60.0))
    idx = max(0, min(idx, len(hourly) - 1))

    period = hourly[idx] if isinstance(hourly[idx], dict) else {}
    if not period:
        return weather

    projected = dict(weather)
    projected["_etaForecast"] = {
        "etaMinutes": round(eta),
        "hourlyIndex": idx,
        "name": period.get("name"),
        "startTime": period.get("startTime"),
        "shortForecast": period.get("shortForecast"),
        "detailedForecast": period.get("detailedForecast"),
        "temperature": period.get("temperature"),
        "windSpeed": period.get("windSpeed"),
        "probabilityOfPrecipitation": period.get("probabilityOfPrecipitation"),
    }

    projected["condition"] = (
        period.get("shortForecast")
        or period.get("detailedForecast")
        or weather.get("condition")
    )

    pop = period.get("probabilityOfPrecipitation")
    if isinstance(pop, dict) and pop.get("value") is not None:
        projected["precipChance"] = pop.get("value")

    if period.get("temperature") is not None:
        current = projected.get("current") if isinstance(projected.get("current"), dict) else {}
        current = dict(current)
        current["temperatureF"] = period.get("temperature")
        projected["current"] = current

    return projected


def _score_point(weather: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    reasons = []

    watchman = weather.get("watchman") or {}
    threat_score = _num(watchman.get("threat_score") or watchman.get("threatScore"))
    if threat_score is not None:
        score += int(threat_score)

    alerts = weather.get("alerts") or []
    if isinstance(alerts, list) and alerts:
        score += min(45, len(alerts) * 20)

        alert_names = []
        for a in alerts[:3]:
            if isinstance(a, dict):
                name = a.get("event") or a.get("headline") or "weather alert"
                if name:
                    alert_names.append(str(name).strip())

        if alert_names:
            reasons.append("; ".join(alert_names))
        else:
            reasons.append(f"{len(alerts)} active alert(s)")

    condition = _text(
        weather.get("condition")
        or weather.get("shortForecast")
        or _dig(weather, ["current", "condition"])
        or _dig(weather, ["forecast", "shortForecast"])
    )

    lower = condition.lower()
    risk_terms = [
        ("tornado", 100),
        ("severe thunderstorm", 85),
        ("thunderstorm", 45),
        ("lightning", 55),
        ("hail", 70),
        ("flood", 70),
        ("heavy rain", 55),
        ("fog", 35),
        ("wind", 35),
        ("snow", 45),
        ("ice", 65),
    ]

    for term, pts in risk_terms:
        if term in lower:
            score += pts
            reasons.append(term)

    precip = _num(weather.get("precipChance") or weather.get("precip_chance") or _dig(weather, ["current", "precipChance"]))
    if precip is not None and precip >= 60:
        score += 20
        reasons.append(f"{int(precip)}% precipitation chance")

    score = max(0, min(score, 100))

    if score >= 75:
        verdict = "dangerous"
    elif score >= 40:
        verdict = "caution"
    else:
        verdict = "clear"

    return {
        "score": score,
        "verdict": verdict,
        "reasons": reasons[:6],
        "condition": condition,
    }


def plan_route_weather(origin_lat: Any, origin_lon: Any, destination: str, samples: int = 5) -> Dict[str, Any]:
    o_lat = _num(origin_lat)
    o_lon = _num(origin_lon)

    if o_lat is None or o_lon is None:
        return {"ok": False, "error": "origin_gps_required"}

    dest = _destination_to_gps(destination)
    if not dest.get("ok"):
        return dest

    d_lat = float(dest["lat"])
    d_lon = float(dest["lon"])

    points = _sample_points(o_lat, o_lon, d_lat, d_lon, samples)
    total_miles = _distance_miles(o_lat, o_lon, d_lat, d_lon)

    scanned = []
    worst_score = 0
    worst_point = None

    for point in points:
        try:
            from app import _fetch_weather_direct
            weather = weather_lookup_for_gps("Route point", point["lat"], point["lon"], _fetch_weather_direct)
            risk = _score_point(weather if isinstance(weather, dict) else {})
        except Exception as exc:
            weather = {"error": str(exc)[:200]}
            risk = {"score": 0, "verdict": "unknown", "reasons": ["weather lookup failed"], "condition": ""}

        mile_marker = total_miles * point["progress"]

        item = {
            **point,
            "mile": round(mile_marker, 1),
            "risk": risk,
            "weather": weather,
        }

        scanned.append(item)

        if risk.get("score", 0) > worst_score:
            worst_score = risk.get("score", 0)
            worst_point = item

    if worst_score >= 75:
        verdict = "dangerous"
        recommendation = "I would not start this drive unless it is necessary. Weather risk is high somewhere on the route."
    elif worst_score >= 40:
        verdict = "caution"
        recommendation = "Use caution. Watchman found weather risk along the route."
    else:
        verdict = "clear"
        recommendation = "Route looks acceptable from the sampled weather points."

    summary = {
        "verdict": verdict,
        "score": worst_score,
        "recommendation": recommendation,
        "worstPoint": worst_point,
        "distanceMiles": round(total_miles, 1),
        "sampleCount": len(scanned),
    }

    return {
        "ok": True,
        "mode": "Watchman Route Planner",
        "origin": {"lat": o_lat, "lon": o_lon},
        "destination": {"name": destination, "lat": d_lat, "lon": d_lon},
        "summary": summary,
        "points": scanned,
    }



def _route_alert_expires_minutes(weather: Dict[str, Any]) -> Any:
    from datetime import datetime, timezone
    alerts = weather.get("alerts") or []
    if not isinstance(alerts, list):
        return None

    now = datetime.now(timezone.utc)
    best = None

    for a in alerts:
        if not isinstance(a, dict):
            continue

        raw = (
            a.get("expires")
            or a.get("ends")
            or a.get("end")
            or a.get("effectiveExpires")
        )

        if not raw:
            continue

        try:
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            mins = round((dt - now).total_seconds() / 60)
            if mins >= 0 and (best is None or mins < best):
                best = mins
        except Exception:
            continue

    return best


def _route_alert_active_at_eta(weather: Dict[str, Any], eta_minutes: float) -> bool:
    expires = _route_alert_expires_minutes(weather)
    if expires is None:
        return True
    return expires >= max(0, eta_minutes - 20)


def _route_eta_label(minutes: Any) -> str:
    try:
        minutes = int(minutes or 0)
    except Exception:
        return "ETA unknown"
    h = minutes // 60
    m = minutes % 60
    if h <= 0:
        return f"{m} min from departure"
    if m == 0:
        return f"{h} hr from departure"
    return f"{h} hr {m} min from departure"

def _route_alert_text(weather: Dict[str, Any], risk: Dict[str, Any]) -> str:
    parts = []
    for a in (weather.get("alerts") or []):
        if isinstance(a, dict):
            parts.extend([
                str(a.get("event") or ""),
                str(a.get("headline") or ""),
                str(a.get("description") or ""),
                str(a.get("instruction") or ""),
                str(a.get("areaDesc") or ""),
            ])
    parts.extend(str(x) for x in (risk.get("reasons") or []))
    parts.append(str(risk.get("condition") or ""))
    return " ".join(parts).lower()


def _route_hazard_policy(weather: Dict[str, Any], risk: Dict[str, Any], eta_minutes: float) -> Dict[str, Any]:
    text = _route_alert_text(weather, risk)
    eta_text = _route_eta_label(eta_minutes)
    active_at_eta = _route_alert_active_at_eta(weather, eta_minutes)

    closure_terms = [
        "road closed", "road closure", "closed due to", "impassable",
        "do not travel", "travel is prohibited", "blocked road",
        "icy road", "ice covered", "black ice", "freezing rain",
    ]

    avoid_terms = [
        "tornado warning",
        "flash flood warning",
        "blizzard warning",
        "ice storm warning",
        "winter storm warning",
        "freezing rain",
        "whiteout",
        "hurricane warning",
        "evacuation",
    ]

    caution_terms = [
        "severe thunderstorm warning",
        "severe thunderstorm",
        "flash flood watch",
        "flood watch",
        "winter weather advisory",
        "dense fog",
        "high wind",
        "heavy rain",
        "thunderstorm",
    ]

    if any(term in text for term in closure_terms):
        return {
            "action": "avoid",
            "reason": "Possible road closure or unsafe road condition",
            "driverMessage": "Avoid this segment if possible. Road impact beats ETA logic.",
            "etaMessage": eta_text,
        }

    if any(term in text for term in avoid_terms):
        if active_at_eta:
            return {
                "action": "avoid",
                "reason": "Dangerous route hazard overlaps estimated arrival time",
                "driverMessage": "Reroute or delay. Watchman expects this hazard to matter when you arrive.",
                "etaMessage": eta_text,
            }
        return {
            "action": "monitor",
            "reason": "Dangerous alert appears likely to expire before arrival",
            "driverMessage": "Monitor only. Watchman does not expect this hazard to still matter when you arrive.",
            "etaMessage": eta_text,
        }

    if any(term in text for term in caution_terms):
        if active_at_eta:
            return {
                "action": "caution",
                "reason": "Driving weather concern overlaps estimated arrival time",
                "driverMessage": "Use caution, but stay on the normal route unless conditions worsen.",
                "etaMessage": eta_text,
            }
        return {
            "action": "monitor",
            "reason": "Driving weather alert appears likely to expire before arrival",
            "driverMessage": "Monitor only. Watchman does not expect this alert to still matter when you arrive.",
            "etaMessage": eta_text,
        }

    info_terms = [
        "heat advisory",
        "air quality",
        "special weather statement",
        "weather advisory",
    ]

    if any(term in text for term in info_terms):
        return {
            "action": "monitor",
            "reason": "Weather information, not a reroute-level driving hazard",
            "driverMessage": "Monitor only. Watchman would not reroute for this.",
            "etaMessage": eta_text,
        }

    return {
        "action": "monitor",
        "reason": "No reroute-level hazard detected",
        "driverMessage": "Monitor only.",
        "etaMessage": eta_text,
    }


def _route_corridor_timeline(weather_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    points = weather_points or []
    if not points:
        return {
            "segments": [],
            "firstConcern": None,
            "worstStretch": None,
            "plainSummary": "No route weather samples are available yet.",
        }

    segments = []
    first_concern = None
    worst = None

    for point in points:
        risk = point.get("risk") or {}
        score = risk.get("score") or 0
        verdict = risk.get("verdict") or "unknown"
        action = point.get("routeAction") or "monitor"
        reasons = risk.get("reasons") or []
        condition = risk.get("condition") or ""

        try:
            score_num = int(score)
        except Exception:
            score_num = 0

        label = "clear"
        if action == "avoid" or score_num >= 75:
            label = "avoid"
        elif action == "caution" or score_num >= 40:
            label = "caution"
        elif action == "monitor" and (reasons or condition):
            label = "monitor"

        segment = {
            "mile": point.get("mile"),
            "etaMinutes": point.get("etaMinutes"),
            "etaMessage": point.get("etaMessage"),
            "status": label,
            "verdict": verdict,
            "score": score_num,
            "condition": condition,
            "reasons": reasons[:5],
            "driverMessage": point.get("driverMessage"),
            "explanation": point.get("explanation"),
        }
        segments.append(segment)

        if label in ["avoid", "caution"] and first_concern is None:
            first_concern = segment

        if worst is None or score_num > (worst.get("score") or 0):
            worst = segment

    concern_segments = [x for x in segments if x.get("status") in ["avoid", "caution"]]
    if concern_segments:
        first = concern_segments[0]
        last = concern_segments[-1]
        plain = (
            f"Watchman sampled the route corridor and found the first driving-weather concern "
            f"near mile {first.get('mile')}. Worst sampled stretch is near mile {(worst or {}).get('mile')} "
            f"with score {(worst or {}).get('score')}/100."
        )
        if first is not last:
            plain += f" Concern signals continue through about mile {last.get('mile')}."
    else:
        plain = "Watchman sampled the route corridor and found no caution-or-avoid weather segment."

    return {
        "segments": segments,
        "firstConcern": first_concern,
        "worstStretch": worst,
        "plainSummary": plain,
    }


def _route_choice_sort_key(candidate: Dict[str, Any]):
    # Priority:
    # 1. Avoid routes with closure / ice / tornado / flash-flood style hazards.
    # 2. If avoid hazards are equal, use the faster normal route.
    # 3. Use caution count only as a tie-breaker.
    return (
        candidate.get("avoidCount", 0),
        candidate.get("durationMinutes", 999999),
        candidate.get("cautionCount", 0),
        candidate.get("avgScore", 0),
    )

def _route_stop_categories() -> List[str]:
    return ["gas", "food", "hospital", "hotel", "pharmacy"]


def route_stop_intelligence(nav: Dict[str, Any]) -> Dict[str, Any]:
    nav = nav if isinstance(nav, dict) else {}
    route = nav.get("route") or {}
    points = nav.get("weatherPoints") or []
    destination = (nav.get("destination") or {}).get("name") or "destination"

    if not nav.get("ok"):
        return {
            "ok": False,
            "mode": "Watchman Route Stop Intelligence",
            "answer": "Route stop intelligence needs a valid navigation route first.",
            "stops": {},
        }

    if not points:
        return {
            "ok": True,
            "mode": "Watchman Route Stop Intelligence",
            "destination": destination,
            "answer": "Route stop intelligence is ready, but no sampled route points are available yet.",
            "stops": {},
        }

    distance = route.get("distanceMiles")
    duration = route.get("durationMinutes")

    candidate_points = []
    for p in points:
        mile = p.get("mile")
        progress = p.get("progress")
        risk = p.get("risk") or {}
        candidate_points.append({
            "mile": mile,
            "progress": progress,
            "etaMinutes": p.get("etaMinutes"),
            "lat": p.get("lat"),
            "lon": p.get("lon"),
            "riskScore": risk.get("score"),
            "riskVerdict": risk.get("verdict"),
            "condition": risk.get("condition"),
            "serviceSearchRadiusMiles": 8,
        })

    safe_candidates = [
        p for p in candidate_points
        if (p.get("riskScore") or 0) < 75 and p.get("lat") is not None and p.get("lon") is not None
    ]

    if not safe_candidates:
        safe_candidates = [p for p in candidate_points if p.get("lat") is not None and p.get("lon") is not None]

    preferred = []
    for target in [0.25, 0.5, 0.75]:
        best = None
        for p in safe_candidates:
            try:
                delta = abs(float(p.get("progress") or 0) - target)
            except Exception:
                delta = 999
            if best is None or delta < best[0]:
                best = (delta, p)
        if best and best[1] not in preferred:
            preferred.append(best[1])

    stops = {}
    for category in _route_stop_categories():
        stops[category] = {
            "category": category,
            "status": "route_search_ready",
            "searchPoints": preferred,
            "note": (
                "This prepares route-aware stop search points. Live place lookup can use these points "
                "without replacing the existing near-me local services flow."
            ),
        }

    parts = [f"Route stop intelligence for {destination}: ready."]
    if distance is not None:
        parts.append(f"Route is about {distance} miles.")
    if duration is not None:
        parts.append(f"ETA is about {round(duration)} minutes.")
    if preferred:
        miles = ", ".join(str(x.get("mile")) for x in preferred if x.get("mile") is not None)
        parts.append(f"Prepared stop-search zones near mile {miles}.")
    parts.append("Categories ready: gas, food, hospital, hotel, pharmacy.")

    return {
        "ok": True,
        "mode": "Watchman Route Stop Intelligence",
        "destination": destination,
        "distanceMiles": distance,
        "durationMinutes": duration,
        "preferredSearchPoints": preferred,
        "stops": stops,
        "answer": " ".join(parts),
    }


def optimize_departure_windows(origin_lat: Any, origin_lon: Any, destination: str, samples: int = 6) -> Dict[str, Any]:
    offsets = [
        ("now", 0),
        ("in 1 hour", 60),
        ("in 2 hours", 120),
        ("in 3 hours", 180),
    ]

    base = build_navigation_route(origin_lat, origin_lon, destination, samples)
    if not base.get("ok"):
        return base

    route = base.get("route") or {}
    weather_points = base.get("weatherPoints") or []

    options = []
    for label, depart_offset in offsets:
        projected_points = []
        total_score = 0
        worst = None

        for point in weather_points:
            original_eta = point.get("etaMinutes") or 0
            adjusted_eta = original_eta + depart_offset
            weather = point.get("weather") or {}

            eta_weather = _route_weather_at_eta(weather, adjusted_eta)
            risk = _score_point(eta_weather if isinstance(eta_weather, dict) else {})

            projected = dict(point)
            projected["departureLabel"] = label
            projected["adjustedEtaMinutes"] = adjusted_eta
            projected["etaForecast"] = (eta_weather or {}).get("_etaForecast") if isinstance(eta_weather, dict) else None
            projected["risk"] = risk

            projected_points.append(projected)
            total_score += risk.get("score", 0) or 0

            if worst is None or (risk.get("score", 0) or 0) > (worst.get("risk", {}).get("score", 0) or 0):
                worst = projected

        avg = round(total_score / max(1, len(projected_points)), 1)
        worst_score = (worst or {}).get("risk", {}).get("score", 0) or 0

        if worst_score >= 75:
            verdict = "delay"
        elif worst_score >= 40:
            verdict = "caution"
        else:
            verdict = "go"

        options.append({
            "label": label,
            "departureOffsetMinutes": depart_offset,
            "verdict": verdict,
            "worstScore": worst_score,
            "averageScore": avg,
            "worstPoint": worst,
        })

    options.sort(key=lambda x: (x.get("worstScore", 999), x.get("averageScore", 999), x.get("departureOffsetMinutes", 999)))
    best = options[0] if options else None

    answer = "Departure optimizer unavailable."
    if best:
        answer = (
            f"Best departure window for {destination}: {best['label']}. "
            f"Worst route risk is {best['worstScore']}/100. "
            f"Verdict: {best['verdict']}."
        )

    return {
        "ok": True,
        "mode": "Watchman Departure Optimizer",
        "destination": base.get("destination"),
        "route": route,
        "options": options,
        "bestDeparture": best,
        "answer": answer,
    }


def build_navigation_route(origin_lat: Any, origin_lon: Any, destination: str, samples: int = 6) -> Dict[str, Any]:
    import json
    import urllib.request

    o_lat = _num(origin_lat)
    o_lon = _num(origin_lon)

    if o_lat is None or o_lon is None:
        return {"ok": False, "error": "origin_gps_required"}

    dest = _destination_to_gps(destination)
    if not dest.get("ok"):
        return dest

    d_lat = float(dest["lat"])
    d_lon = float(dest["lon"])

    osrm_urls = [
        (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{o_lon},{o_lat};{d_lon},{d_lat}"
            "?overview=full&geometries=geojson&steps=true&alternatives=true"
        ),
        (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{o_lon},{o_lat};{d_lon},{d_lat}"
            "?overview=simplified&geometries=geojson&steps=true&alternatives=true"
        ),
        (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{o_lon},{o_lat};{d_lon},{d_lat}"
            "?overview=simplified&geometries=geojson&steps=false&alternatives=false"
        ),
    ]

    route_data = None
    last_error = ""

    for osrm_url in osrm_urls:
        try:
            req = urllib.request.Request(osrm_url, headers={"User-Agent": "ChapNetAI-Watchman-Navigation/1.0"})
            with urllib.request.urlopen(req, timeout=35) as res:
                route_data = json.loads(res.read().decode("utf-8"))
            if route_data.get("routes"):
                break
        except Exception as exc:
            last_error = str(exc)[:300]

    if not route_data:
        return {
            "ok": False,
            "error": "road_route_temporarily_unavailable",
            "details": last_error or "The public road router did not return a route. Try again or choose a less remote destination.",
            "destination": {"name": destination, "lat": d_lat, "lon": d_lon},
            "origin": {"lat": o_lat, "lon": o_lon},
        }

    routes = route_data.get("routes") or []
    if not routes:
        return {"ok": False, "error": "no_route_found"}

    analyzed_routes = []

    for route_index, candidate in enumerate(routes[:3], 1):
        coords = (((candidate.get("geometry") or {}).get("coordinates")) or [])
        latlon = [{"lat": c[1], "lon": c[0]} for c in coords if isinstance(c, list) and len(c) >= 2]

        sample_points = _sample_route_geometry(latlon, samples)
        weather_points = []

        distance_miles = (candidate.get("distance") or 0) / 1609.344
        duration_minutes = (candidate.get("duration") or 0) / 60

        for i, point in enumerate(sample_points, 1):
            mile = round(distance_miles * point["progress"], 1)
            eta_minutes = round(duration_minutes * point["progress"])

            try:
                from app import _fetch_weather_direct
                weather = weather_lookup_for_gps("Route point", point["lat"], point["lon"], _fetch_weather_direct)
                eta_weather = _route_weather_at_eta(weather if isinstance(weather, dict) else {}, eta_minutes)
                risk = _score_point(eta_weather if isinstance(eta_weather, dict) else {})
            except Exception as exc:
                weather = {"error": str(exc)[:200]}
                eta_weather = {}
                risk = {"score": 0, "verdict": "unknown", "reasons": ["weather lookup failed"], "condition": ""}

            policy = _route_hazard_policy(weather if isinstance(weather, dict) else {}, risk, eta_minutes)

            weather_points.append({
                "index": i,
                "lat": point["lat"],
                "lon": point["lon"],
                "progress": point["progress"],
                "mile": mile,
                "etaMinutes": eta_minutes,
                "risk": risk,
                "etaForecast": (eta_weather or {}).get("_etaForecast") if isinstance(eta_weather, dict) else None,
                "risk": risk,
                "routeAction": policy.get("action"),
                "routeActionReason": policy.get("reason"),
                "driverMessage": policy.get("driverMessage"),
                "etaMessage": policy.get("etaMessage"),
                "explanation": ", ".join(risk.get("reasons") or []) or "No major weather risk detected.",
            })

        worst = None
        total_score = 0
        hazard_count = 0
        avoid_count = 0
        caution_count = 0

        for point in weather_points:
            score = point.get("risk", {}).get("score", 0) or 0
            total_score += score

            if point.get("routeAction") == "avoid":
                avoid_count += 1
                hazard_count += 1
            elif point.get("routeAction") == "caution":
                caution_count += 1
                hazard_count += 1
            elif score >= 70:
                hazard_count += 1

            if worst is None or score > worst.get("risk", {}).get("score", 0):
                worst = point

        max_score = (worst or {}).get("risk", {}).get("score", 0)
        avg_score = round(total_score / max(1, len(weather_points)), 1)

        analyzed_routes.append({
            "routeIndex": route_index,
            "route": candidate,
            "latlon": latlon,
            "weatherPoints": weather_points,
            "worstPoint": worst,
            "maxScore": max_score,
            "avgScore": avg_score,
            "hazardCount": hazard_count,
            "avoidCount": avoid_count,
            "cautionCount": caution_count,
            "distanceMiles": round((candidate.get("distance") or 0) / 1609.344, 1),
            "durationMinutes": round((candidate.get("duration") or 0) / 60),
        })

    analyzed_routes.sort(key=_route_choice_sort_key)

    chosen = analyzed_routes[0]
    route = chosen["route"]
    latlon = chosen["latlon"]
    weather_points = chosen["weatherPoints"]
    worst = chosen["worstPoint"]
    worst_score = chosen["maxScore"]

    steps = []
    for leg in route.get("legs") or []:
        for step in leg.get("steps") or []:
            maneuver = step.get("maneuver") or {}
            loc = maneuver.get("location") or []
            steps.append({
                "instruction": _route_instruction(step),
                "name": step.get("name") or "",
                "distanceMeters": round(step.get("distance") or 0),
                "durationSeconds": round(step.get("duration") or 0),
                "lat": loc[1] if len(loc) >= 2 else None,
                "lon": loc[0] if len(loc) >= 2 else None,
                "type": maneuver.get("type") or "",
                "modifier": maneuver.get("modifier") or "",
            })

    avoid_count = chosen.get("avoidCount", 0)
    caution_count = chosen.get("cautionCount", 0)

    if avoid_count:
        verdict = "dangerous"
        recommendation = "Avoid or delay if possible. Watchman found a reroute-level hazard such as closure, ice, tornado, flash flooding, or severe winter travel risk."
    elif caution_count:
        verdict = "caution"
        recommendation = "Use caution. Watchman found weather concerns, but no automatic-reroute hazard on the selected route."
    else:
        verdict = "clear"
        recommendation = "Fastest available route selected. No reroute-level weather hazard detected."

    route_choices = []
    for r in analyzed_routes:
        route_choices.append({
            "routeIndex": r["routeIndex"],
            "selected": r is chosen,
            "distanceMiles": r["distanceMiles"],
            "durationMinutes": r["durationMinutes"],
            "maxRisk": r["maxScore"],
            "averageRisk": r["avgScore"],
            "hazardPoints": r["hazardCount"],
            "avoidPoints": r.get("avoidCount", 0),
            "cautionPoints": r.get("cautionCount", 0),
            "worstMile": (r["worstPoint"] or {}).get("mile"),
            "worstReason": (r["worstPoint"] or {}).get("explanation"),
        })

    corridor = _route_corridor_timeline(weather_points)

    return {
        "ok": True,
        "mode": "Watchman Safest Weather Route",
        "origin": {"lat": o_lat, "lon": o_lon},
        "destination": {"name": destination, "lat": d_lat, "lon": d_lon},
        "route": {
            "distanceMiles": chosen["distanceMiles"],
            "durationMinutes": chosen["durationMinutes"],
            "geometry": latlon,
            "steps": steps,
        },
        "weatherPoints": weather_points,
        "routeChoices": route_choices,
        "summary": {
            "verdict": verdict,
            "score": worst_score,
            "recommendation": recommendation,
            "worstPoint": worst,
            "routeChoice": "Watchman compared available route options and selected the best weather route.",
            "routesCompared": len(analyzed_routes),
            "corridorTimeline": corridor,
            "corridorSummary": corridor.get("plainSummary"),
            "firstConcern": corridor.get("firstConcern"),
            "worstStretch": corridor.get("worstStretch"),
        },
    }


def _sample_route_geometry(points: List[Dict[str, float]], count: int) -> List[Dict[str, Any]]:
    if not points:
        return []
    count = max(3, min(int(count or 8), 16))
    if len(points) <= count:
        return [{**p, "progress": i / max(1, len(points) - 1)} for i, p in enumerate(points)]

    out = []
    for i in range(count):
        idx = round((len(points) - 1) * (i / (count - 1)))
        p = points[idx]
        out.append({"lat": p["lat"], "lon": p["lon"], "progress": i / (count - 1)})
    return out


def _route_instruction(step: Dict[str, Any]) -> str:
    maneuver = step.get("maneuver") or {}
    typ = maneuver.get("type") or "continue"
    mod = maneuver.get("modifier") or ""
    road = step.get("name") or "the road"

    if typ == "depart":
        return f"Start on {road}"
    if typ == "arrive":
        return "Arrive at your destination"
    if typ == "turn":
        return f"Turn {mod} onto {road}".strip()
    if typ == "new name":
        return f"Continue onto {road}"
    if typ == "roundabout":
        return f"Enter the roundabout and continue toward {road}"
    if typ == "merge":
        return f"Merge {mod} onto {road}".strip()
    if typ == "on ramp":
        return f"Take the ramp onto {road}"
    if typ == "off ramp":
        return f"Take the exit ramp toward {road}"
    if typ == "fork":
        return f"Keep {mod} toward {road}".strip()
    return f"Continue on {road}"
