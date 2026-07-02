from .employment_dashboard import employment_dashboard, format_dashboard_text
from .employment_reports import employment_operations_report

def run_employment_operations_center():
    dashboard = employment_dashboard()
    report = employment_operations_report()

    return {
        "center": "Watchman Employment Operations Center",
        "dashboard": dashboard,
        "report": report,
        "dashboard_text": format_dashboard_text(dashboard)
    }
