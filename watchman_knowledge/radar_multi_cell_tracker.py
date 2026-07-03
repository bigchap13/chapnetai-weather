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
    return math.degrees(lat_rad), lon


def _distance_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bearing(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return round((math.degrees(math.atan2(x, y)) + 360) % 360)


def _rainviewer_frames():
    data = requests.get(
        "https://api.rainviewer.com/public/weather-maps.json",
        timeout=10,
    ).json()
    past = ((data.get("radar") or {}).get("past") or [])[-4:]
    return {
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


def _extract_cells_for_frame(host, path, lat, lon, zoom=7, radius_tiles=1):
    cx, cy = _latlon_to_tile(lat, lon, zoom)
    buckets = {}

    for tx in range(cx - radius_tiles, cx + radius_tiles + 1):
        for ty in range(cy - radius_tiles, cy + radius_tiles + 1):
            img = _download_tile(host, path, zoom, tx, ty)
            if img is None:
                continue

            px = img.load()
            width, height = img.size

            for y in range(0, height, 8):
                for x in range(0, width, 8):
                    r, g, b, a = px[x, y]
                    if a < 40:
                        continue

                    intensity = max(r, g, b)
                    if intensity < 70:
                        continue

                    global_x = tx + (x / width)
                    global_y = ty + (y / height)
                    plat, plon = _tile_to_latlon(global_x, global_y, zoom)

                    # Bucket by rough lat/lon region to separate storm blobs.
                    key = (round(plat * 5) / 5, round(plon * 5) / 5)
                    item = buckets.setdefault(key, {
                        "weight": 0.0,
                        "latSum": 0.0,
                        "lonSum": 0.0,
                        "pixels": 0,
                        "maxIntensity": 0,
                    })

                    weight = max(1, intensity - 60)
                    item["weight"] += weight
                    item["latSum"] += plat * weight
                    item["lonSum"] += plon * weight
                    item["pixels"] += 1
                    item["maxIntensity"] = max(item["maxIntensity"], intensity)

    cells = []
    for key, item in buckets.items():
        if item["pixels"] < 6 or item["weight"] <= 0:
            continue

        clat = item["latSum"] / item["weight"]
        clon = item["lonSum"] / item["weight"]
        distance = _distance_miles(lat, lon, clat, clon)

        cells.append({
            "lat": round(clat, 5),
            "lon": round(clon, 5),
            "pixels": item["pixels"],
            "weight": round(item["weight"], 2),
            "maxIntensity": item["maxIntensity"],
            "distanceFromPlaceMiles": round(distance, 2),
            "bucket": [key[0], key[1]],
        })

    cells.sort(key=lambda c: (c["distanceFromPlaceMiles"], -c["weight"]))
    return cells[:8]


def radar_multi_cell_tracker(place, lat, lon):
    lat = _safe_float(lat)
    lon = _safe_float(lon)

    try:
        rv = _rainviewer_frames()
    except Exception as e:
        return {
            "mode": "Watchman Multi-Cell Storm Tracker V1",
            "ok": False,
            "error": str(e),
            "place": place,
        }

    frames = rv.get("frames") or []
    if len(frames) < 2:
        return {
            "mode": "Watchman Multi-Cell Storm Tracker V1",
            "ok": False,
            "error": "not_enough_radar_frames",
            "place": place,
        }

    host = rv["host"]
    prev_frame, cur_frame = frames[-2], frames[-1]

    prev_cells = _extract_cells_for_frame(host, prev_frame.get("path"), lat, lon)
    cur_cells = _extract_cells_for_frame(host, cur_frame.get("path"), lat, lon)

    tracks = []
    used_prev = set()

    minutes = max(1, (int(cur_frame.get("time") or 0) - int(prev_frame.get("time") or 0)) / 60)

    for idx, cur in enumerate(cur_cells):
        best_i = None
        best_d = None

        for pi, prev in enumerate(prev_cells):
            if pi in used_prev:
                continue
            d = _distance_miles(prev["lat"], prev["lon"], cur["lat"], cur["lon"])
            if best_d is None or d < best_d:
                best_i = pi
                best_d = d

        if best_i is None or best_d is None or best_d > 45:
            tracks.append({
                "cellId": f"cell-{idx+1}",
                "status": "new_or_unmatched",
                "current": cur,
                "confidence": 45,
            })
            continue

        used_prev.add(best_i)
        prev = prev_cells[best_i]
        speed = round(best_d / (minutes / 60), 1)
        bearing = _bearing(prev["lat"], prev["lon"], cur["lat"], cur["lon"])

        confidence = 55
        if cur["pixels"] >= 10 and prev["pixels"] >= 10:
            confidence += 15
        if speed <= 90:
            confidence += 10
        if best_d >= 0.25:
            confidence += 10

        tracks.append({
            "cellId": f"cell-{idx+1}",
            "status": "tracked",
            "previous": prev,
            "current": cur,
            "bearingDegrees": bearing,
            "speedMph": speed,
            "distanceMovedMiles": round(best_d, 2),
            "minutesBetweenFrames": round(minutes, 1),
            "confidence": min(confidence, 90),
            "strengthTrend": (
                "strengthening" if cur["weight"] > prev["weight"] * 1.15
                else "weakening" if cur["weight"] < prev["weight"] * 0.85
                else "steady"
            ),
        })

    tracked = [t for t in tracks if t.get("status") == "tracked"]

    return {
        "mode": "Watchman Multi-Cell Storm Tracker V1",
        "ok": True,
        "time": _now(),
        "place": place,
        "center": {"lat": lat, "lon": lon},
        "cellCount": len(cur_cells),
        "trackedCount": len(tracked),
        "tracks": tracks,
        "previousCells": prev_cells,
        "currentCells": cur_cells,
        "rainviewer": {
            "generated": rv.get("generated"),
            "previousFrame": prev_frame.get("time"),
            "currentFrame": cur_frame.get("time"),
            "frameCount": len(frames),
        },
        "answer": f"Multi-Cell Tracker V1 found {len(cur_cells)} active radar cell(s) near {place}, with {len(tracked)} tracked between frames.",
        "note": "V1 separates radar precipitation into multiple rough cells and tracks nearest matches frame-to-frame. Split/merge logic is next.",
    }
