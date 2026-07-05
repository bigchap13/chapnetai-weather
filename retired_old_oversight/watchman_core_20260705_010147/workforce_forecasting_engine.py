from .employment_success_metrics import employment_success_metrics
from .workforce_intelligence import workforce_intelligence
from .partner_dashboard import partner_dashboard

def workforce_forecasting_engine():
    metrics = employment_success_metrics()
    intel = workforce_intelligence()
    partners = partner_dashboard()

    projected_hires = max(
        metrics.get("hires", 0),
        int(metrics.get("interviews", 0) * 0.5),
        int(metrics.get("applications", 0) * 0.25)
    )

    placement_pressure = "normal"

    if intel.get("residents_seeking_work", 0) > intel.get("job_leads_available", 0):
        placement_pressure = "high"

    if intel.get("job_leads_available", 0) == 0:
        placement_pressure = "critical"

    return {
        "projected_hires": projected_hires,
        "placement_pressure": placement_pressure,
        "residents_seeking_work": intel.get("residents_seeking_work", 0),
        "job_leads_available": intel.get("job_leads_available", 0),
        "employer_partners": partners.get("active_partners", 0),
        "forecast_status": "generated"
    }
