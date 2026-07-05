from .ai_oversight import ai_oversight_snapshot, ai_governance_summary
from .approval_queue import default_approval_queue

def generate_ai_brief():
    snapshot = ai_oversight_snapshot()
    summary = ai_governance_summary(snapshot)
    approvals = default_approval_queue()

    return {
        "summary": summary,
        "health_checks": snapshot["health_checks"],
        "approval_queue": approvals
    }

def format_ai_brief_text(brief):
    s = brief["summary"]

    lines = [
        s["title"],
        "",
        f"Status: {s['status']}",
        f"Total Agents: {s['total_agents']}",
        f"Online Agents: {s['online_agents']}",
        f"Planned Agents: {s['planned_agents']}",
        f"Offline Agents: {s['offline_agents']}",
        f"Human Approvals Required: {s['human_approvals_required']}",
        f"Escalations Required: {s['escalations_required']}",
        "",
        "Health Checks:"
    ]

    for item in brief["health_checks"]:
        lines.append(f"- {item['agent_id']}: {item['health']} — {item['message']}")

    lines.append("")
    lines.append("Approval Queue:")

    for item in brief["approval_queue"]:
        lines.append(f"- {item['priority'].upper()}: {item['title']} ({item['system']})")

    return "\n".join(lines)
