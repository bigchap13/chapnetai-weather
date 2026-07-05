from .jj_badges import earned_badges, next_badge
from .jj_wellness import wellness_status
from .jj_graduation import graduation_readiness
from .jj_transportation import transportation_summary
from .jj_integration import jj_summary

def resident_brief(resident):
    return {
        "sol_id": resident.get("sol_id"),
        "track": resident.get("track"),
        "stage": resident.get("stage"),
        "readiness_score": resident.get("readiness_score"),
        "meetings": resident.get("meetings"),
        "savings": resident.get("savings"),
        "employment_status": resident.get("employment_status"),
        "badges": earned_badges(resident),
        "next_badge": next_badge(resident),
        "wellness": wellness_status(resident),
        "graduation": graduation_readiness(resident)
    }

def executive_jj_brief(residents):
    return {
        "title": "Joshua's Journey Executive Brief",
        "summary": jj_summary(residents),
        "transportation": transportation_summary(residents),
        "graduation_candidates": [r.get("sol_id") for r in residents if graduation_readiness(r)["graduation_ready"]],
        "resident_briefs": [resident_brief(r) for r in residents]
    }

def format_executive_jj_brief(brief):
    s = brief["summary"]

    lines = [
        "JOSHUA'S JOURNEY EXECUTIVE BRIEF",
        "",
        f"Residents Active: {s['residents_active']}",
        f"Average Readiness: {s['average_readiness']}",
        f"Employment Ready: {s['employment_ready']}",
        f"Transportation Requests: {s['transportation_requests']}",
        f"Wellness Alerts: {s['wellness_alerts']}",
        "",
        "Graduation Candidates:",
    ]

    if brief["graduation_candidates"]:
        for sol_id in brief["graduation_candidates"]:
            lines.append(f"- {sol_id}")
    else:
        lines.append("- None yet")

    return "\n".join(lines)
