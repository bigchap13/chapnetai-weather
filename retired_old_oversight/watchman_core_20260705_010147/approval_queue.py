from datetime import datetime

def create_approval_item(title, system, requested_by, reason, priority="normal"):
    return {
        "title": title,
        "system": system,
        "requested_by": requested_by,
        "reason": reason,
        "priority": priority,
        "status": "pending",
        "created": datetime.now().isoformat(timespec="seconds")
    }

def default_approval_queue():
    return [
        create_approval_item(
            "Activate Joshua Journey Support Bot",
            "Joshua's Journey",
            "Watchman",
            "Support bot should not activate without human leadership approval.",
            "high"
        ),
        create_approval_item(
            "Enable Governance Bot",
            "ChapNetAI",
            "Watchman",
            "Governance review system requires human approval before enforcement.",
            "normal"
        )
    ]
