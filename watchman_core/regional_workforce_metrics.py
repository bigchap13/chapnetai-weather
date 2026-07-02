from .regional_employment_network import regional_employment_network

def regional_workforce_metrics():
    regions = regional_employment_network()

    return {
        "regions_total": len(regions),
        "active_regions": len([r for r in regions if r["status"] == "active"]),
        "planned_regions": len([r for r in regions if r["status"] == "planned"]),
        "total_employer_partners": sum(r["employer_partners"] for r in regions),
        "total_open_positions": sum(r["open_positions"] for r in regions),
        "total_residents_seeking_work": sum(r["residents_seeking_work"] for r in regions)
    }
