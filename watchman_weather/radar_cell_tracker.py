import io
import math
import requests
from datetime import datetime, timezone
from PIL import Image


def _now():
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d


def _latlon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def _tile_to_latlon(x, y, zoom):
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def _bearing(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)

    return round((math.degrees(math.atan2(x, y)) + 360) % 360)


def _distance_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _rainviewer_frames():
    data = requests.get(
        "https://api.rainviewer.com/public/weather-maps.json",
        timeout=10,
    ).json()

    past = ((data.get("radar") or {}).get("past") or [])[-4:]

    return {
        "ok": True,
        "generated": data.get("generated"),
        "host": data.get("host") or "https://tilecache.rainviewer.com",
        "frames": past,
    }


def _download_tile(host, path, z, x, y):
    url = f"{host}{path}/256/{z}/{x}/{y}/2/1_1.png"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return None
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def _precip_centroid_for_frame(host, path, lat, lon, zoom=7, radius_tiles=1):
    cx, cy = _latlon_to_tile(lat, lon, zoom)

    weighted_lat = 0.0
    weighted_lon = 0.0
    weight_total = 0.0
    precip_pixels = 0
    sampled_tiles = 0

    for tx in range(cx - radius_tiles, cx + radius_tiles + 1):
        for ty in range(cy - radius_tiles, cy + radius_tiles + 1):
            img = _download_tile(host, path, zoom, tx, ty)
            if img is None:
                continue

            sampled_tiles += 1
            px = img.load()
            width, height = img.size

            for y in range(0, height, 8):
                for x in range(0, width, 8):
                    r, g, b, a = px[x, y]
                    if a < 40:
                        continue

                    intensity = max(r, g, b)
                    # RainViewer radar pixels are colored. Ignore nearly transparent/dark map noise.
                    if intensity < 65:
                        continue

                    # Weight stronger radar colors more heavily.
                    weight = max(1, intensity - 60)
                    global_x = tx + (x / width)
                    global_y = ty + (y / height)
                    plat, plon = _tile_to_latlon(global_x, global_y, zoom)

                    weighted_lat += plat * weight
                    weighted_lon += plon * weight
                    weight_total += weight
                    precip_pixels += 1

    if weight_total <= 0:
        return {
            "detected": False,
            "sampledTiles": sampled_tiles,
            "precipPixels": precip_pixels,
        }

    return {
        "detected": True,
        "sampledTiles": sampled_tiles,
        "precipPixels": precip_pixels,
        "lat": round(weighted_lat / weight_total, 5),
        "lon": round(weighted_lon / weight_total, 5),
        "weight": round(weight_total, 2),
    }


def radar_cell_tracker(place, lat, lon):
    lat = _safe_float(lat)
    lon = _safe_float(lon)

    try:
        rv = _rainviewer_frames()
    except Exception as e:
        return {
            "mode": "Watchman Radar Cell Tracker V1",
            "ok": False,
            "error": str(e),
            "place": place,
        }

    frames = rv.get("frames") or []
    if len(frames) < 2:
        return {
            "mode": "Watchman Radar Cell Tracker V1",
            "ok": False,
            "error": "not_enough_radar_frames",
            "place": place,
            "rainviewer": rv,
        }

    host = rv.get("host") or "https://tilecache.rainviewer.com"
    recent = frames[-2:]

    scans = []
    for f in recent:
        path = f.get("path")
        if not path:
            continue
        scan = _precip_centroid_for_frame(host, path, lat, lon)
        scan["frameTime"] = f.get("time")
        scan["path"] = path
        scans.append(scan)

    valid = [s for s in scans if s.get("detected")]

    if len(valid) < 2:
        return {
            "mode": "Watchman Radar Cell Tracker V1",
            "ok": True,
            "place": place,
            "detected": False,
            "reason": "precipitation centroid not detected in enough frames",
            "scans": scans,
            "rainviewer": {
                "generated": rv.get("generated"),
                "frameCount": len(frames),
            },
            "note": "Radar frames were available, but no strong cell centroid was detected near the watched location.",
        }

    a, b = valid[-2], valid[-1]
    minutes = max(1, (int(b.get("frameTime") or 0) - int(a.get("frameTime") or 0)) / 60)
    distance = _distance_miles(a["lat"], a["lon"], b["lat"], b["lon"])
    speed = round(distance / (minutes / 60), 1)
    bearing = _bearing(a["lat"], a["lon"], b["lat"], b["lon"])

    confidence = 50
    if a.get("precipPixels", 0) > 20 and b.get("precipPixels", 0) > 20:
        confidence += 20
    if speed <= 80:
        confidence += 10
    if distance > 0.5:
        confidence += 10
    confidence = min(confidence, 90)

    return {
        "mode": "Watchman Radar Cell Tracker V1",
        "ok": True,
        "detected": True,
        "time": _now(),
        "place": place,
        "center": {"lat": lat, "lon": lon},
        "cell": {
            "previous": {"lat": a["lat"], "lon": a["lon"], "time": a.get("frameTime")},
            "current": {"lat": b["lat"], "lon": b["lon"], "time": b.get("frameTime")},
            "bearingDegrees": bearing,
            "speedMph": speed,
            "distanceMovedMiles": round(distance, 2),
            "minutesBetweenFrames": round(minutes, 1),
            "confidence": confidence,
            "precipPixelsPrevious": a.get("precipPixels"),
            "precipPixelsCurrent": b.get("precipPixels"),
        },
        "scans": scans,
        "rainviewer": {
            "generated": rv.get("generated"),
            "frameCount": len(frames),
        },
        "answer": (
            f"Radar Cell Tracker V1 detected a precipitation centroid moving "
            f"{bearing} degrees at about {speed} mph. Confidence: {confidence}%."
        ),
        "note": "This is true radar-frame centroid tracking, not just forecast wording. It is still V1 and does not yet split multiple storm cells.",
    }
