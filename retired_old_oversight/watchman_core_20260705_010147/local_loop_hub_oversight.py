import json
from pathlib import Path
from datetime import datetime

LOCAL_LOOP_DIR = Path.home() / "local-loop-hub"
COMMUNITY_DATA = LOCAL_LOOP_DIR / "community_data.json"
DATA_FILE = LOCAL_LOOP_DIR / "data.json"
OUTPUT_FILE = Path("watchman_v102_local_loop_hub_oversight.json")


def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as exc:
        return {"_error": str(exc)}


def count_unread(items):
    return sum(1 for item in items if not item.get("read", False))


def build_local_loop_oversight():
    community = load_json(COMMUNITY_DATA)
    data = load_json(DATA_FILE)

    alerts = community.get("alerts", [])
    notifications = community.get("notifications", [])
    messages = community.get("messages", [])
    requests = community.get("community_requests", [])
    commerce = community.get("community_commerce", [])

    unread_notifications = count_unread(notifications)
    unread_direct_messages = sum(
        1 for msg in messages
        if msg.get("to", "").strip().lower() == "brandon chappell"
        and not msg.get("read_by_recipient", True)
    )

    risks = []
    recommendations = []

    if "_error" in community:
        risks.append("Community data file could not be read.")
        recommendations.append("Inspect local-loop-hub/community_data.json for JSON corruption.")

    if "_error" in data:
        risks.append("Core data file could not be read.")
        recommendations.append("Inspect local-loop-hub/data.json for JSON corruption.")

    if unread_notifications > 0:
        risks.append(f"{unread_notifications} unread platform notification(s) require review.")
        recommendations.append("Review the Notifications Center and mark reviewed items read.")

    if unread_direct_messages > 0:
        risks.append(f"{unread_direct_messages} unread direct message(s) require response.")
        recommendations.append("Open the direct message bubble and respond to pending messages.")

    if not alerts:
        recommendations.append("No active alert stream found. Maintain at least one test alert workflow for validation.")

    if not requests:
        recommendations.append("Community Requests Board is empty or unavailable. Verify request intake if expected activity is missing.")

    health = "Healthy"
    if risks:
        health = "Watch"

    report = {
        "module": "Watchman V102 Local Loop Hub Oversight",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "local_loop_path": str(LOCAL_LOOP_DIR),
        "health": health,
        "metrics": {
            "alerts": len(alerts),
            "notifications": len(notifications),
            "unread_notifications": unread_notifications,
            "direct_messages": len(messages),
            "unread_direct_messages": unread_direct_messages,
            "community_requests": len(requests),
            "commerce_listings": len(commerce),
            "posts": len(data.get("posts", [])) if isinstance(data, dict) else 0,
        },
        "risks": risks,
        "recommendations": recommendations,
        "latest_alerts": alerts[-5:] if isinstance(alerts, list) else [],
        "latest_notifications": notifications[-5:] if isinstance(notifications, list) else [],
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = build_local_loop_oversight()
    print(json.dumps(report, indent=2))
