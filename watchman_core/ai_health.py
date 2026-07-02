def evaluate_agent_health(agent):
    status = agent.get("status", "unknown")
    health = agent.get("health", "yellow")

    if status == "offline":
        return {
            "agent_id": agent.get("agent_id"),
            "health": "red",
            "message": f"{agent.get('name')} is offline.",
            "requires_escalation": True
        }

    if health == "red":
        return {
            "agent_id": agent.get("agent_id"),
            "health": "red",
            "message": f"{agent.get('name')} reports red health.",
            "requires_escalation": True
        }

    if status == "planned":
        return {
            "agent_id": agent.get("agent_id"),
            "health": "yellow",
            "message": f"{agent.get('name')} is planned but not active.",
            "requires_escalation": False
        }

    return {
        "agent_id": agent.get("agent_id"),
        "health": "green",
        "message": f"{agent.get('name')} is operating normally.",
        "requires_escalation": False
    }

def evaluate_all_agents(agents):
    return [evaluate_agent_health(agent) for agent in agents]
