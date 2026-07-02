def smart_home_alert(title, message, priority="normal"):
    return {
        "title": title,
        "message": message,
        "priority": priority,
        "source": "smart_home",
        "status": "open"
    }

def evaluate_smart_home(devices):
    alerts = []
    for device in devices:
        if device.get("status") == "offline":
            alerts.append(
                smart_home_alert(
                    "Device Offline",
                    f"{device.get('name')} is offline.",
                    "medium"
                )
            )
    return alerts
