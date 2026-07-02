from .outreach_tracker import outreach_tracker
from .followup_scheduler import followup_schedule

def outreach_dashboard():
    records = outreach_tracker()
    followups = followup_schedule()

    return {
        "organizations": len(records),
        "followups": len(followups),
        "records": records,
        "status": "operational"
    }

def format_outreach_dashboard(data):
    lines = [
        "WATCHMAN VEHICLE DONATION OUTREACH TRACKER",
        "",
        f"Organizations: {data['organizations']}",
        f"Follow-Ups Pending: {data['followups']}",
        "",
        "OUTREACH:"
    ]

    for record in data["records"]:
        lines.append(
            f"- {record['organization']} | {record['contact_status']} | Next: {record['next_action']}"
        )

    return "\n".join(lines)
