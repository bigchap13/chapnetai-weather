from .employment_dashboard import employment_dashboard

def employment_operations_report():
    dashboard = employment_dashboard()
    metrics = dashboard["scorecard"]["metrics"]

    return {
        "report": "Employment Operations Report",
        "status": dashboard["scorecard"]["status"],
        "priority": dashboard["scorecard"]["priority"],
        "metrics": metrics,
        "alerts": dashboard["alerts"]
    }
