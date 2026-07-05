from __future__ import annotations

import base64
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

DATA_DIR = Path("data")
SUBSCRIPTION_PATH = DATA_DIR / "watchman_web_push_subscriptions.json"
KEY_PATH = DATA_DIR / "watchman_web_push_vapid.json"


def _now() -> int:
    return int(time.time())


def _load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else default
    except Exception:
        return default


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def _urlsafe_b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _generate_vapid_keys() -> Dict[str, str]:
    """
    Generates VAPID keys if cryptography is available through pywebpush deps.
    If not available, returns disabled status without breaking the app.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        private_num = private_key.private_numbers().private_value.to_bytes(32, "big")
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

        return {
            "ok": True,
            "privateKey": _urlsafe_b64(private_num),
            "publicKey": _urlsafe_b64(public_bytes),
            "createdAt": _now(),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc)[:200],
            "publicKey": "",
            "privateKey": "",
            "createdAt": _now(),
        }


def get_vapid_public_key() -> Dict[str, Any]:
    keys = _load_json(KEY_PATH, {})
    if not keys:
        keys = _generate_vapid_keys()
        _save_json(KEY_PATH, keys)
    return {
        "ok": bool(keys.get("ok") and keys.get("publicKey")),
        "publicKey": keys.get("publicKey", ""),
        "enabled": bool(keys.get("ok") and keys.get("publicKey")),
        "error": keys.get("error"),
    }


def _clean_device_id(device_id: Optional[str]) -> str:
    if not device_id:
        return "watchman-device-" + uuid.uuid4().hex[:24]
    safe = "".join(ch for ch in str(device_id) if ch.isalnum() or ch in "-_")
    return safe[:80] or ("watchman-device-" + uuid.uuid4().hex[:24])


def save_subscription(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = _load_json(SUBSCRIPTION_PATH, {"subscriptions": {}})
    device_id = _clean_device_id(payload.get("deviceId") or payload.get("device_id"))
    subscription = payload.get("subscription")

    if not isinstance(subscription, dict) or not subscription.get("endpoint"):
        return {"ok": False, "error": "subscription_required", "deviceId": device_id}

    data.setdefault("subscriptions", {})
    data["subscriptions"][device_id] = {
        "deviceId": device_id,
        "subscription": subscription,
        "updatedAt": _now(),
        "userAgent": str(payload.get("userAgent") or "")[:300],
    }
    _save_json(SUBSCRIPTION_PATH, data)
    return {"ok": True, "deviceId": device_id, "enabled": True}


def get_subscription(device_id: str) -> Dict[str, Any]:
    data = _load_json(SUBSCRIPTION_PATH, {"subscriptions": {}})
    clean = _clean_device_id(device_id)
    sub = data.get("subscriptions", {}).get(clean)
    return {"ok": True, "deviceId": clean, "hasSubscription": bool(sub), "subscription": sub}


def send_web_push(device_id: str, title: str, body: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean = _clean_device_id(device_id)
    data = _load_json(SUBSCRIPTION_PATH, {"subscriptions": {}})
    sub_record = data.get("subscriptions", {}).get(clean)
    keys = _load_json(KEY_PATH, {})

    if not sub_record:
        return {"ok": False, "sent": False, "reason": "no_subscription", "deviceId": clean}
    if not keys.get("ok") or not keys.get("privateKey"):
        return {"ok": False, "sent": False, "reason": "vapid_not_ready", "deviceId": clean}

    try:
        from pywebpush import webpush, WebPushException

        payload = {
            "title": title,
            "body": body,
            "deviceId": clean,
            "url": "/",
            "extra": extra or {},
        }

        webpush(
            subscription_info=sub_record["subscription"],
            data=json.dumps(payload),
            vapid_private_key=keys["privateKey"],
            vapid_claims={"sub": "mailto:watchman@chapnetai.local"},
        )
        return {"ok": True, "sent": True, "deviceId": clean}
    except Exception as exc:
        return {
            "ok": False,
            "sent": False,
            "reason": "send_failed",
            "deviceId": clean,
            "error": str(exc)[:300],
        }


def status() -> Dict[str, Any]:
    subs = _load_json(SUBSCRIPTION_PATH, {"subscriptions": {}})
    vapid = get_vapid_public_key()
    return {
        "ok": True,
        "webPushEnabled": bool(vapid.get("enabled")),
        "subscriptionCount": len(subs.get("subscriptions", {})),
        "vapid": {"enabled": bool(vapid.get("enabled")), "error": vapid.get("error")},
    }
