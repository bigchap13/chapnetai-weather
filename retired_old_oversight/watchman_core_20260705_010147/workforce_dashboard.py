from .workforce_intelligence import workforce_intelligence, workforce_readiness_score
from .workforce_forecaster import workforce_forecast
from .intervention_queue import intervention_queue

def workforce_dashboard():
    return {
        "intelligence": workforce_intelligence(),
        "readiness_score": workforce_readiness_score(),
        "forecast": workforce_forecast(),
        "interventions": intervention_queue()
    }

def format_workforce_dashboard(data):
    intel = data["intelligence"]

    return f"""
WATCHMAN WORKFORCE INTELLIGENCE

Readiness Score: {data['readiness_score']}

Residents Seeking Work: {intel['residents_seeking_work']}
Job Leads: {intel['job_leads_available']}
Applications: {intel['applications_active']}
Interviews: {intel['interviews']}
Hires: {intel['hires']}

Employer Partners: {intel['employer_partners']}
Open Positions: {intel['open_positions']}

Projected Hires: {data['forecast']['projected_hires']}

Interventions: {len(data['interventions'])}
""".strip()
