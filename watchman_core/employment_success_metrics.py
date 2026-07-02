from .job_pipeline import sample_pipeline

def employment_success_metrics():
    pipeline = sample_pipeline()

    applied = len([p for p in pipeline if p.get("stage") in [
        "Applied",
        "Interview Scheduled",
        "Interview Completed",
        "Offer Received",
        "Hired",
        "Retained 30 Days"
    ]])

    interviews = len([p for p in pipeline if "Interview" in p.get("stage", "")])
    offers = len([p for p in pipeline if p.get("stage") == "Offer Received"])
    hired = len([p for p in pipeline if p.get("stage") == "Hired"])
    retained = len([p for p in pipeline if p.get("stage") == "Retained 30 Days"])

    return {
        "applications": applied,
        "interviews": interviews,
        "offers": offers,
        "hires": hired,
        "retained_30_days": retained,
        "interview_rate": round((interviews / applied) * 100, 2) if applied else 0,
        "hire_rate": round((hired / applied) * 100, 2) if applied else 0,
        "retention_rate": round((retained / hired) * 100, 2) if hired else 0
    }
