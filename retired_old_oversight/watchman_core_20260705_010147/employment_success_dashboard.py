from .employment_success_metrics import employment_success_metrics
from .employment_outcomes import employment_outcome_summary

def employment_success_dashboard():
    metrics = employment_success_metrics()
    outcome = employment_outcome_summary()

    return {
        "dashboard": "Employment Success Analytics",
        "status": outcome["status"],
        "metrics": metrics
    }

def format_success_dashboard(data):
    m = data["metrics"]

    return f"""
WATCHMAN EMPLOYMENT SUCCESS ANALYTICS

Status: {data['status']}

Applications: {m['applications']}
Interviews: {m['interviews']}
Offers: {m['offers']}
Hires: {m['hires']}
Retained 30 Days: {m['retained_30_days']}

Interview Rate: {m['interview_rate']}%
Hire Rate: {m['hire_rate']}%
Retention Rate: {m['retention_rate']}%
""".strip()
