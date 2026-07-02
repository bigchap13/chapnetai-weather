from .employment_metrics import employment_scorecard
from .employment_alerts import employment_alerts
from .employment_briefings import executive_employment_brief

def employment_dashboard():
    return {
        "dashboard": "Watchman Employment Operations Center",
        "scorecard": employment_scorecard(),
        "alerts": employment_alerts(),
        "brief": executive_employment_brief()
    }

def format_dashboard_text(dashboard):
    metrics = dashboard["scorecard"]["metrics"]

    lines = [
        "WATCHMAN EMPLOYMENT OPERATIONS CENTER",
        "",
        f"Residents Seeking Work: {metrics['residents_seeking_work']}",
        f"Job Leads Available: {metrics['job_leads_available']}",
        f"Employer Partners: {metrics['employer_partners']}",
        f"Applications Active: {metrics['applications_active']}",
        f"Interviews: {metrics['interviews']}",
        f"Offers Received: {metrics['offers_received']}",
        f"Hires: {metrics['hires']}",
        f"Retained 30 Days: {metrics['retained_30_days']}",
        "",
        "ALERTS:"
    ]

    alerts = dashboard["alerts"]
    if alerts:
        for a in alerts:
            lines.append(f"- {a['level'].upper()}: {a['message']}")
    else:
        lines.append("- No active employment alerts.")

    return "\n".join(lines)
