from .employment_success_metrics import employment_success_metrics

def employment_outcome_summary():
    metrics = employment_success_metrics()

    if metrics["hires"] > 0:
        status = "placements_active"
    elif metrics["interviews"] > 0:
        status = "interviews_in_progress"
    elif metrics["applications"] > 0:
        status = "applications_active"
    else:
        status = "pipeline_building"

    return {
        "status": status,
        "metrics": metrics
    }
