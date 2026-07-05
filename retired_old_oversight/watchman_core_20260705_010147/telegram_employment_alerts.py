def alert_new_job_lead(job):
    return {
        "type": "NEW_JOB_LEAD",
        "message": f"New Job Lead: {job.get('title')} | {job.get('employer')}"
    }

def alert_application_submitted(sol_id, job_id):
    return {
        "type": "APPLICATION_SUBMITTED",
        "message": f"{sol_id} applied for {job_id}"
    }

def alert_interview_scheduled(sol_id, job_id):
    return {
        "type": "INTERVIEW_SCHEDULED",
        "message": f"{sol_id} interview scheduled for {job_id}"
    }

def alert_offer_received(sol_id, job_id):
    return {
        "type": "OFFER_RECEIVED",
        "message": f"{sol_id} received an offer for {job_id}"
    }

def alert_hired(sol_id, job_id):
    return {
        "type": "HIRED",
        "message": f"{sol_id} hired for {job_id}"
    }

def alert_retained(sol_id, job_id):
    return {
        "type": "RETAINED_30_DAYS",
        "message": f"{sol_id} retained 30 days at {job_id}"
    }

def alert_intervention(sol_id, reason):
    return {
        "type": "INTERVENTION_REQUIRED",
        "message": f"{sol_id} requires employment intervention: {reason}"
    }
