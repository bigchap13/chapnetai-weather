from .workforce_registry import sample_workforce_profiles
from .workforce_readiness import workforce_readiness

def workforce_summary():
    profiles = sample_workforce_profiles()

    readiness = [workforce_readiness(p) for p in profiles]

    return {
        "participants": len(profiles),
        "job_ready": len([r for r in readiness if r["level"] == "Job Ready"]),
        "training_ready": len([r for r in readiness if r["level"] == "Training Ready"]),
        "foundation_needed": len([r for r in readiness if r["level"] == "Foundation Needed"])
    }
