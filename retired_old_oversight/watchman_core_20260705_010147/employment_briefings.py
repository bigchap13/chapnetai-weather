from .job_leads import sample_job_leads
from .employer_partners import sample_employer_partners
from .job_pipeline import sample_pipeline
from .jj_integration import sample_residents
from .job_matching import match_jobs

def employment_summary():
    residents = sample_residents()
    job_leads = sample_job_leads()
    employers = sample_employer_partners()
    pipeline = sample_pipeline()

    seeking = [r for r in residents if r.get("employment_status") in ["Seeking Work", "Ready"]]
    hired = [p for p in pipeline if p.get("stage") == "Hired"]
    interviews = [p for p in pipeline if "Interview" in p.get("stage", "")]

    return {
        "residents_seeking_work": len(seeking),
        "job_leads_available": len(job_leads),
        "employer_partners": len(employers),
        "applications_active": len(pipeline),
        "interviews": len(interviews),
        "hired": len(hired)
    }

def resident_job_brief(resident):
    return {
        "sol_id": resident.get("sol_id"),
        "employment_status": resident.get("employment_status"),
        "matches": match_jobs(resident)
    }

def executive_employment_brief():
    residents = sample_residents()
    summary = employment_summary()

    return {
        "title": "Watchman Job Connection Brief",
        "summary": summary,
        "resident_job_briefs": [resident_job_brief(r) for r in residents]
    }

def format_employment_brief(brief):
    s = brief["summary"]

    lines = [
        "WATCHMAN JOB CONNECTION BRIEF",
        "",
        f"Residents Seeking Work: {s['residents_seeking_work']}",
        f"Job Leads Available: {s['job_leads_available']}",
        f"Employer Partners: {s['employer_partners']}",
        f"Applications Active: {s['applications_active']}",
        f"Interviews: {s['interviews']}",
        f"Hired: {s['hired']}",
    ]

    return "\n".join(lines)
