from .telegram_employment_alerts import (
    alert_new_job_lead,
    alert_application_submitted,
    alert_interview_scheduled,
    alert_offer_received,
    alert_hired,
    alert_retained,
    alert_intervention
)

def sample_notifications():
    return [
        alert_new_job_lead({
            "title": "Warehouse Associate",
            "employer": "Future Employer Partner"
        }),
        alert_application_submitted("SOL-00001", "JOB-001"),
        alert_interview_scheduled("SOL-00001", "JOB-001")
    ]
