from .community_partner_registry import community_partner_registry
from .partner_contact_history import sample_contact_history
from .partner_followups import partner_followups
from .partner_scorecard import partner_scorecard

def community_crm_dashboard():
    partners = community_partner_registry()
    history = sample_contact_history()
    followups = partner_followups()
    scores = partner_scorecard()

    return {
        "dashboard": "Community Partnership CRM",
        "partners": len(partners),
        "contact_records": len(history),
        "followups_pending": len([f for f in followups if f["status"] == "pending"]),
        "partners_list": partners,
        "contact_history": history,
        "followups": followups,
        "scorecards": scores,
        "status": "operational"
    }

def format_community_crm_dashboard(data):
    lines = [
        "WATCHMAN COMMUNITY PARTNERSHIP CRM",
        "",
        f"Partners: {data['partners']}",
        f"Contact Records: {data['contact_records']}",
        f"Follow-Ups Pending: {data['followups_pending']}",
        "",
        "PARTNERS:"
    ]

    for partner in data["scorecards"]:
        lines.append(
            f"- {partner['name']} | {partner['category']} | {partner['status']} | Score: {partner['score']}"
        )

    lines.append("")
    lines.append("FOLLOW-UPS:")

    for followup in data["followups"]:
        lines.append(
            f"- {followup['partner_id']} | {followup['next_action']} | {followup['status']}"
        )

    return "\n".join(lines)
