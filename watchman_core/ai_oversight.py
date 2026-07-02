from .ai_registry import default_agents
from .ai_health import evaluate_all_agents

def ai_oversight_snapshot(agents=None):
    if agents is None:
        agents = default_agents()

    health_checks = evaluate_all_agents(agents)

    total = len(agents)
    online = len([a for a in agents if a.get("status") == "online"])
    planned = len([a for a in agents if a.get("status") == "planned"])
    offline = len([a for a in agents if a.get("status") == "offline"])
    approvals = len([a for a in agents if a.get("requires_human_approval")])
    escalations = len([h for h in health_checks if h.get("requires_escalation")])

    return {
        "agents": agents,
        "health_checks": health_checks,
        "total_agents": total,
        "online_agents": online,
        "planned_agents": planned,
        "offline_agents": offline,
        "human_approvals_required": approvals,
        "escalations_required": escalations
    }

def ai_governance_summary(snapshot):
    if snapshot.get("escalations_required", 0) > 0:
        status = "ATTENTION REQUIRED"
    elif snapshot.get("human_approvals_required", 0) > 0:
        status = "HUMAN REVIEW PENDING"
    else:
        status = "GREEN"

    return {
        "title": "AI OVERSIGHT SUMMARY",
        "status": status,
        "total_agents": snapshot.get("total_agents", 0),
        "online_agents": snapshot.get("online_agents", 0),
        "planned_agents": snapshot.get("planned_agents", 0),
        "offline_agents": snapshot.get("offline_agents", 0),
        "human_approvals_required": snapshot.get("human_approvals_required", 0),
        "escalations_required": snapshot.get("escalations_required", 0)
    }
