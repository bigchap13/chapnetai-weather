from .employment_metrics import employment_metrics

def employment_alerts():
    m = employment_metrics()
    alerts = []

    if m["residents_seeking_work"] > m["job_leads_available"]:
        alerts.append({
            "level": "attention",
            "message": "More residents are seeking work than current job leads available."
        })

    if m["interviews"] == 0 and m["applications_active"] > 0:
        alerts.append({
            "level": "watch",
            "message": "Applications are active but no interviews are currently scheduled."
        })

    if m["hires"] == 0:
        alerts.append({
            "level": "watch",
            "message": "No residents have reached hired status yet."
        })

    return alerts
