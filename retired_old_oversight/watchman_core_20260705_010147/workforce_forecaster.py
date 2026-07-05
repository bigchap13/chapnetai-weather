from .workforce_intelligence import workforce_intelligence

def workforce_forecast():
    intel = workforce_intelligence()

    projected_hires = max(
        intel["interviews"],
        int(intel["applications_active"] * 0.25)
    )

    return {
        "projected_hires": projected_hires,
        "open_positions": intel["open_positions"],
        "status": "forecast_generated"
    }
