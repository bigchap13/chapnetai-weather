from .regional_employment_network import regional_employment_network

def regional_employer_map():
    regions = regional_employment_network()

    return {
        "map": "Regional Employer Network Map",
        "regions": regions,
        "active_regions": len([r for r in regions if r["status"] == "active"]),
        "planned_regions": len([r for r in regions if r["status"] == "planned"])
    }
