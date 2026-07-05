def workforce_readiness(profile):
    score = profile.get("readiness_score", 0)

    if score >= 85:
        level = "Job Ready"
    elif score >= 70:
        level = "Training Ready"
    else:
        level = "Foundation Needed"

    return {
        "sol_id": profile.get("sol_id"),
        "level": level,
        "score": score
    }
