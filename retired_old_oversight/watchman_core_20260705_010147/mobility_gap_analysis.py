from .mobility_metrics import mobility_metrics

def mobility_gap_analysis():
    metrics = mobility_metrics()
    gaps = []

    if metrics["needs_driver"] > 0:
        gaps.append({
            "level": "high",
            "gap": "Ride requests need drivers",
            "recommendation": "Assign volunteer driver or partner dispatch."
        })

    if metrics["medical_rides"] > 0:
        gaps.append({
            "level": "medium",
            "gap": "Medical transportation demand present",
            "recommendation": "Track Birmingham medical appointment rides separately."
        })

    if metrics["mobility_partners"] < 3:
        gaps.append({
            "level": "medium",
            "gap": "Limited mobility partner network",
            "recommendation": "Expand dealership, church, volunteer, and employer transportation partners."
        })

    return {
        "gap_count": len(gaps),
        "gaps": gaps
    }
