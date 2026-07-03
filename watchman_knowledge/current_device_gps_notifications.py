from __future__ import annotations

import json
import time
import uuid
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path("data")
STORE_PATH = DATA_DIR / "watchman_current_devices.json"

THREAT_THRESHOLD = 45
MIN_NOTIFY_SECONDS = 15 * 60


def _now() -> int:
    return int(time.time())


def _load() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        return {"devices": {}, "pushes": []}
    try:
        data = json.loads(STORE_PATH.read_text())
        if not isinstance(data, dict):
            return {"devices": {}, "pushes": []}
        data.setdefault("devices", {})
        data.setdefault("pushes", [])
        return data
    except Exception:
        return {"devices": {}, "pushes": []}


def _save(data: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))


def _clean_device_id(device_id: Optional[str]) -> str:
    if not device_id:
        return "watchman-device-" + uuid.uuid4().hex[:24]
    safe = "".join(ch for ch in str(device_id) if ch.isalnum() or ch in "-_")
    return safe[:80] or ("watchman-device-" + uuid.uuid4().hex[:24])


def _float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except Exception:
        return None


def _basic_risk(lat: float, lon: float) -> Dict[str, Any]:
    """
    Current-device GPS risk check.

    Uses the user's own browser-approved coordinates and checks active NWS
    alerts for that point. No city is hard-coded.
    """
    reasons: List[str] = []
    alerts: List[Dict[str, Any]] = []

    try:
        url = "https://api.weather.gov/alerts/active?" + urllib.parse.urlencode(
            {"point": f"{lat:.4f},{lon:.4f}"}
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ChapNetAI-Watchman/1.0 current-device-gps-alerts",
                "Accept": "application/geo+json, application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as res:
            payload = json.loads(res.read().decode("utf-8", "replace"))

        for feature in payload.get("features", [])[:8]:
            props = feature.get("properties", {}) or {}
            event = str(props.get("event") or "Weather Alert")
            severity = str(props.get("severity") or "Unknown")
            urgency = str(props.get("urgency") or "Unknown")
            certainty = str(props.get("certainty") or "Unknown")
            alerts.append(
                {
                    "event": event,
                    "severity": severity,
                    "urgency": urgency,
                    "certainty": certainty,
                    "headline": str(props.get("headline") or event)[:220],
                }
            )
    except Exception as exc:
        signature = f"gps-risk-unavailable:{round(lat, 2)}:{round(lon, 2)}"
        return {
            "score": 0,
            "risk": "checking",
            "reasons": ["NWS alert check unavailable"],
            "signature": signature,
            "active_alert_count": 0,
            "alerts": [],
            "source": "nws_active_alerts_by_current_device_gps",
            "error": str(exc)[:160],
        }

    score = 0
    for alert in alerts:
        severity = alert.get("severity", "").lower()
        urgency = alert.get("urgency", "").lower()
        event = alert.get("event", "")
        if severity == "extreme":
            score += 80
        elif severity == "severe":
            score += 65
        elif severity == "moderate":
            score += 45
        elif severity == "minor":
            score += 25
        else:
            score += 15

        if urgency == "immediate":
            score += 20
        elif urgency == "expected":
            score += 10

        reasons.append(event)

    score = min(score, 100)
    risk = "quiet"
    if score >= 75:
        risk = "danger"
    elif score >= 45:
        risk = "elevated"
    elif score > 0:
        risk = "watch"

    alert_names = "|".join(sorted(a.get("event", "") for a in alerts))
    signature = f"nws-alerts:{round(lat, 2)}:{round(lon, 2)}:{len(alerts)}:{alert_names}"

    return {
        "score": score,
        "risk": risk,
        "reasons": reasons[:5],
        "signature": signature,
        "active_alert_count": len(alerts),
        "alerts": alerts,
        "source": "nws_active_alerts_by_current_device_gps",
    }


def register_device(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = _load()
    device_id = _clean_device_id(payload.get("deviceId") or payload.get("device_id"))
    device = data["devices"].get(device_id, {})
    device.update(
        {
            "deviceId": device_id,
            "registeredAt": device.get("registeredAt") or _now(),
            "updatedAt": _now(),
            "notificationPermission": payload.get("notificationPermission"),
            "userAgent": str(payload.get("userAgent") or "")[:300],
        }
    )
    data["devices"][device_id] = device
    _save(data)
    return {"ok": True, "deviceId": device_id, "device": device}


def update_location(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = _load()
    device_id = _clean_device_id(payload.get("deviceId") or payload.get("device_id"))

    lat = _float(payload.get("lat"))
    lon = _float(payload.get("lon"))
    accuracy = _float(payload.get("accuracy"))

    if lat is None or lon is None:
        return {"ok": False, "error": "lat_lon_required", "deviceId": device_id}
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return {"ok": False, "error": "invalid_coordinates", "deviceId": device_id}

    risk = _basic_risk(lat, lon)
    now = _now()

    device = data["devices"].get(device_id, {"deviceId": device_id, "registeredAt": now})
    previous_signature = device.get("lastAlertSignature")
    previous_score = int(device.get("lastRiskScore") or 0)
    last_notification_time = int(device.get("lastNotificationTime") or 0)

    should_push = False
    title = "Watchman Weather Update"
    body = "Watchman is watching weather near your current phone location."

    if risk["score"] >= THREAT_THRESHOLD and previous_score < THREAT_THRESHOLD:
        should_push = True
        title = "Watchman Weather Alert"
        body = "Bad weather risk has increased near your current phone location."
    elif risk["signature"] != previous_signature and risk.get("active_alert_count", 0) > 0:
        should_push = True
        title = "Watchman Alert Change"
        body = "Weather alerts changed near your current phone location."

    if should_push and now - last_notification_time >= MIN_NOTIFY_SECONDS:
        push_id = "gpspush-" + uuid.uuid4().hex
        data["pushes"].append(
            {
                "id": push_id,
                "deviceId": device_id,
                "title": title,
                "body": body,
                "createdAt": now,
                "status": "pending",
                "risk": risk,
            }
        )
        device["lastNotificationTime"] = now

    device.update(
        {
            "deviceId": device_id,
            "updatedAt": now,
            "lastLocation": {
                "lat": lat,
                "lon": lon,
                "accuracy": accuracy,
                "updatedAt": now,
            },
            "lastRisk": risk,
            "lastRiskScore": risk["score"],
            "lastAlertSignature": risk["signature"],
        }
    )

    data["devices"][device_id] = device
    _save(data)

    return {
        "ok": True,
        "deviceId": device_id,
        "lastRisk": risk,
        "pendingCount": len(
            [
                p
                for p in data["pushes"]
                if p.get("deviceId") == device_id and p.get("status") == "pending"
            ]
        ),
        "device": device,
    }


def pending_pushes(device_id: str) -> Dict[str, Any]:
    data = _load()
    clean = _clean_device_id(device_id)
    pushes = [
        p
        for p in data["pushes"]
        if p.get("deviceId") == clean and p.get("status") == "pending"
    ]
    return {"ok": True, "deviceId": clean, "pushes": pushes}


def ack_push(push_id: str, device_id: str) -> Dict[str, Any]:
    data = _load()
    clean = _clean_device_id(device_id)
    changed = False

    for push in data["pushes"]:
        if push.get("id") == push_id and push.get("deviceId") == clean:
            push["status"] = "acked"
            push["ackedAt"] = _now()
            changed = True

    _save(data)
    return {"ok": True, "acked": changed, "deviceId": clean, "id": push_id}


def status(device_id: Optional[str] = None) -> Dict[str, Any]:
    data = _load()
    if device_id:
        clean = _clean_device_id(device_id)
        return {
            "ok": True,
            "deviceId": clean,
            "device": data["devices"].get(clean),
            "pendingCount": len(
                [
                    p
                    for p in data["pushes"]
                    if p.get("deviceId") == clean and p.get("status") == "pending"
                ]
            ),
        }
    return {
        "ok": True,
        "deviceCount": len(data["devices"]),
        "pendingCount": len([p for p in data["pushes"] if p.get("status") == "pending"]),
    }
