from datetime import datetime

def default_agents():
    return [
        {
            "agent_id": "agent-001",
            "name": "Watchman Core",
            "system": "Watchman",
            "role": "Operational Oversight",
            "status": "online",
            "health": "green",
            "last_check": datetime.now().isoformat(timespec="seconds"),
            "requires_human_approval": False
        },
        {
            "agent_id": "agent-002",
            "name": "Joshua Journey Support Bot",
            "system": "Joshua's Journey",
            "role": "Resident Support",
            "status": "planned",
            "health": "yellow",
            "last_check": datetime.now().isoformat(timespec="seconds"),
            "requires_human_approval": True
        },
        {
            "agent_id": "agent-003",
            "name": "Governance Bot",
            "system": "ChapNetAI",
            "role": "Governance Review",
            "status": "planned",
            "health": "yellow",
            "last_check": datetime.now().isoformat(timespec="seconds"),
            "requires_human_approval": True
        }
    ]

def register_agent(agent_id, name, system, role, status="planned", health="yellow"):
    return {
        "agent_id": agent_id,
        "name": name,
        "system": system,
        "role": role,
        "status": status,
        "health": health,
        "last_check": datetime.now().isoformat(timespec="seconds"),
        "requires_human_approval": True
    }
