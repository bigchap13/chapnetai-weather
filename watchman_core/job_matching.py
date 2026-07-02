from .job_leads import sample_job_leads

def match_jobs(resident):
    matches = []

    for job in sample_job_leads():
        if resident.get("employment_status") in ["Seeking Work", "Ready"]:
            matches.append({
                "sol_id": resident.get("sol_id"),
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "employer": job.get("employer"),
                "match_reason": "Resident is seeking work and job is open."
            })

    return matches
