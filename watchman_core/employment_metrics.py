from .employment_briefings import employment_summary
from .job_pipeline import sample_pipeline
from .job_leads import sample_job_leads
from .employer_partners import sample_employer_partners

def employment_metrics():
    summary = employment_summary()
    pipeline = sample_pipeline()
    jobs = sample_job_leads()
    employers = sample_employer_partners()

    offers = [p for p in pipeline if p.get("stage") == "Offer Received"]
    hired = [p for p in pipeline if p.get("stage") == "Hired"]
    retained = [p for p in pipeline if p.get("stage") == "Retained 30 Days"]

    return {
        "residents_seeking_work": summary["residents_seeking_work"],
        "job_leads_available": len(jobs),
        "employer_partners": len(employers),
        "applications_active": len(pipeline),
        "interviews": summary["interviews"],
        "offers_received": len(offers),
        "hires": len(hired),
        "retained_30_days": len(retained)
    }

def employment_scorecard():
    m = employment_metrics()

    return {
        "title": "Employment Operations Scorecard",
        "metrics": m,
        "status": "operational",
        "priority": "job connection and retention"
    }
