from .regional_employer_map import regional_employer_map
from .regional_workforce_metrics import regional_workforce_metrics

def regional_employment_dashboard():
    return {
        "dashboard": "Regional Employment Network",
        "map": regional_employer_map(),
        "metrics": regional_workforce_metrics()
    }

def format_regional_dashboard(data):
    m = data["metrics"]

    lines = [
        "WATCHMAN REGIONAL EMPLOYMENT NETWORK",
        "",
        f"Regions Total: {m['regions_total']}",
        f"Active Regions: {m['active_regions']}",
        f"Planned Regions: {m['planned_regions']}",
        f"Employer Partners: {m['total_employer_partners']}",
        f"Open Positions: {m['total_open_positions']}",
        f"Residents Seeking Work: {m['total_residents_seeking_work']}",
        "",
        "REGIONS:"
    ]

    for region in data["map"]["regions"]:
        lines.append(
            f"- {region['name']} | {region['status']} | Employers: {region['employer_partners']} | Open Positions: {region['open_positions']}"
        )

    return "\n".join(lines)
