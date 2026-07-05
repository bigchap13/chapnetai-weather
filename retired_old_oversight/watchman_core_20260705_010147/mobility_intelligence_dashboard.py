from .mobility_metrics import mobility_metrics
from .mobility_gap_analysis import mobility_gap_analysis

def mobility_intelligence_dashboard():
    return {
        "dashboard": "Community Mobility Intelligence",
        "metrics": mobility_metrics(),
        "gap_analysis": mobility_gap_analysis(),
        "status": "operational"
    }

def format_mobility_intelligence(data):
    m = data["metrics"]
    g = data["gap_analysis"]

    lines = [
        "WATCHMAN COMMUNITY MOBILITY INTELLIGENCE",
        "",
        f"Total Rides: {m['rides_total']}",
        f"Medical Rides: {m['medical_rides']}",
        f"Employment Rides: {m['employment_rides']}",
        f"Scheduled Rides: {m['scheduled_rides']}",
        f"Missed Rides: {m['missed_rides']}",
        f"Needs Driver: {m['needs_driver']}",
        f"Mobility Partners: {m['mobility_partners']}",
        "",
        f"Mobility Gaps: {g['gap_count']}",
        "",
        "GAPS:"
    ]

    if g["gaps"]:
        for item in g["gaps"]:
            lines.append(f"- {item['level'].upper()}: {item['gap']} | {item['recommendation']}")
    else:
        lines.append("- No major mobility gaps detected.")

    return "\n".join(lines)
