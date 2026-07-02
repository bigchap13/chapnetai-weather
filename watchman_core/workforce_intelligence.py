from .partner_dashboard import partner_dashboard
from .employment_metrics import employment_metrics

def workforce_intelligence():
    metrics = employment_metrics()
    partners = partner_dashboard()

    return {
        "residents_seeking_work": metrics["residents_seeking_work"],
        "job_leads_available": metrics["job_leads_available"],
        "applications_active": metrics["applications_active"],
        "interviews": metrics["interviews"],
        "hires": metrics["hires"],
        "employer_partners": partners["active_partners"],
        "open_positions": partners["open_positions"],
        "intelligence_status": "operational"
    }

def workforce_readiness_score():
    intel = workforce_intelligence()

    score = 50

    if intel["job_leads_available"] > 0:
        score += 10

    if intel["employer_partners"] > 0:
        score += 10

    if intel["open_positions"] > 0:
        score += 10

    if intel["applications_active"] > 0:
        score += 10

    if intel["interviews"] > 0:
        score += 10

    return min(score, 100)
